"""AI features: appointment document generation and the specialty guidance chat.

Document pipeline: audio -> transcription -> clinical note -> PDF.
Transcription runs locally (faster-whisper), so the audio never leaves the
machine; only the transcribed text is sent to the model that structures the
note.

Heavy libraries (faster-whisper, anthropic, reportlab) are imported inside
the functions on purpose: importing them at module load would slow down
every Django command (including migrate and the test suite) for no benefit.

Prompts and user-visible strings are in Portuguese by design — the product
UI is pt-BR.
"""
# pylint: disable=import-outside-toplevel
import io
import json
import os

from django.utils import timezone

WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")
CLAUDE_MODEL = "claude-opus-4-8"

# Transcription model cache: loading is expensive and must happen only once.
_CACHE = {}


class TranscriptionUnavailable(RuntimeError):
    """faster-whisper is not installed in this environment."""


class NoteGenerationUnavailable(RuntimeError):
    """ANTHROPIC_API_KEY is not configured."""


def _get_whisper_model():
    """Load the model once per process (loading is expensive)."""
    if "whisper" not in _CACHE:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptionUnavailable(
                "faster-whisper não instalado. Rode: pip install faster-whisper"
            ) from exc
        _CACHE["whisper"] = WhisperModel(
            WHISPER_MODEL_SIZE, device="cpu", compute_type="int8"
        )
    return _CACHE["whisper"]


def transcribe_audio(audio_path):
    """Transcribe an audio file to text (Portuguese)."""
    model = _get_whisper_model()
    segments, _info = model.transcribe(str(audio_path), language="pt", vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments).strip()


SYSTEM_PROMPT = """Você é um assistente que organiza transcrições de consultas \
médicas em notas clínicas estruturadas, em português do Brasil.

Regras:
- Baseie-se exclusivamente no que está na transcrição. Não invente sintomas, \
medicamentos, dosagens, exames ou diagnósticos.
- Se a transcrição não trouxer informação para uma seção, escreva \
"Não relatado" nessa seção.
- Use linguagem clínica objetiva, em terceira pessoa.
- Não inclua conselhos ao paciente nem texto fora das seções pedidas."""

SECTIONS = [
    ("queixa_principal", "Queixa principal"),
    ("historia_doenca_atual", "História da doença atual"),
    ("achados_exame", "Achados do exame"),
    ("hipotese_diagnostica", "Hipótese diagnóstica"),
    ("conduta", "Conduta"),
    ("retorno", "Retorno"),
]

NOTE_SCHEMA = {
    "type": "object",
    "properties": {key: {"type": "string"} for key, _ in SECTIONS},
    "required": [key for key, _ in SECTIONS],
    "additionalProperties": False,
}


def build_medical_note(transcript, api_key=None):
    """Turn the raw transcript into a structured clinical note (dict)."""
    import anthropic

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise NoteGenerationUnavailable(
            "ANTHROPIC_API_KEY não configurada no .env"
        )

    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": NOTE_SCHEMA},
        },
        messages=[{
            "role": "user",
            "content": (
                "Organize a transcrição de consulta abaixo nas seções pedidas.\n\n"
                f"<transcricao>\n{transcript}\n</transcricao>"
            ),
        }],
    )
    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)


def _pdf_styles():
    """Paragraph styles for the document, in MedHelper colors."""
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    base = getSampleStyleSheet()
    deep_blue = colors.HexColor("#2b5f7e")
    return {
        "title": ParagraphStyle(
            "MedTitle", parent=base["Title"], fontSize=18,
            textColor=deep_blue, spaceAfter=2,
        ),
        "heading": ParagraphStyle(
            "MedHeading", parent=base["Heading2"], fontSize=11.5,
            textColor=deep_blue, spaceBefore=14, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "MedBody", parent=base["BodyText"], fontSize=10.5, leading=15,
        ),
        "meta": ParagraphStyle(
            "MedMeta", parent=base["BodyText"], fontSize=9.5,
            textColor=colors.HexColor("#5b6b76"), leading=13,
        ),
    }


def render_note_pdf(appointment, note):
    """Render the appointment document PDF and return its bytes."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    style = _pdf_styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"Consulta #{appointment.id} — MedHelper",
    )

    story = [
        Paragraph("MedHelper", style["title"]),
        Paragraph("Documento de atendimento", style["meta"]),
        Spacer(1, 14),
    ]

    when = timezone.localtime(appointment.appointment_date)
    for label, value in (
        ("Paciente", appointment.patient or "—"),
        ("Médico", appointment.doctor or "—"),
        ("Data da consulta", when.strftime("%d/%m/%Y às %H:%M")),
    ):
        story.append(Paragraph(f"<b>{label}:</b> {value}", style["meta"]))

    story.append(Spacer(1, 6))

    for key, label in SECTIONS:
        story.append(Paragraph(label, style["heading"]))
        story.append(Paragraph(note.get(key) or "Não relatado", style["body"]))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Documento gerado automaticamente a partir da transcrição do "
        "atendimento, com apoio de inteligência artificial. Deve ser revisado "
        "e validado pelo profissional responsável antes de uso clínico.",
        style["meta"],
    ))

    doc.build(story)
    return buffer.getvalue()


def note_to_text(note):
    """Plain-text version of the note, stored in Appointment.transcript."""
    return "\n\n".join(
        f"{label}:\n{note.get(key) or 'Não relatado'}" for key, label in SECTIONS
    )


class AssistantUnavailable(RuntimeError):
    """ANTHROPIC_API_KEY is not configured (guidance chat)."""


CHAT_SYSTEM_PROMPT = """Você é o assistente virtual do MedHelper. Sua única \
função é ajudar o paciente a identificar QUAL ESPECIALIDADE MÉDICA procurar, \
a partir do que ele relata.

Regras:
- Fale somente sobre a escolha de especialidade. Se o paciente puxar qualquer \
outro assunto (diagnósticos, medicamentos, exames, conversa casual, ajuda com \
outras tarefas...), recuse com gentileza e traga a conversa de volta ao tema.
- Não faça diagnóstico nem sugira tratamento ou medicação.
- Se faltar informação para recomendar, faça uma pergunta de esclarecimento \
por vez.
- Ao recomendar, indique a especialidade e explique em uma frase o porquê. \
Especialidades disponíveis nesta clínica: {specialties}. Se nenhuma delas \
atender, diga qual especialidade o paciente deve buscar fora da clínica.
- Diante de sinais de emergência (dor no peito intensa, falta de ar grave, \
confusão súbita, sangramento importante, ideação suicida), oriente procurar \
um pronto-socorro ou ligar 192 imediatamente.
- Responda em português do Brasil, em tom acolhedor, com no máximo 120 \
palavras por mensagem.
- Responda em texto puro, sem formatação markdown (nada de asteriscos, \
listas ou títulos)."""


def specialty_chat_reply(history, specialties=(), api_key=None):
    """Answer one turn of the specialty guidance chat.

    ``history`` is the list of ``{"role", "content"}`` messages ending with
    the patient's message; returns the assistant's reply text.
    """
    import anthropic

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise AssistantUnavailable("ANTHROPIC_API_KEY não configurada no .env")

    listed = ", ".join(specialties) if specialties else "nenhuma cadastrada no momento"
    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1000,
        system=CHAT_SYSTEM_PROMPT.format(specialties=listed),
        thinking={"type": "adaptive"},
        output_config={"effort": "low"},
        messages=list(history),
    )
    reply = next(
        block.text for block in response.content if block.type == "text"
    ).strip()
    # The page renders plain text; strip markdown bold that slips past the prompt.
    return reply.replace("**", "")
