"""Geração do documento da consulta: áudio -> transcrição -> nota clínica -> PDF.

A transcrição roda localmente (faster-whisper), então o áudio nunca sai da
máquina. Só o texto transcrito é enviado ao modelo que estrutura a nota.

As bibliotecas pesadas (faster-whisper, anthropic, reportlab) são importadas
dentro das funções de propósito: carregá-las na importação do módulo deixaria
todo comando do Django (inclusive migrate e os testes) mais lento sem
necessidade.
"""
# pylint: disable=import-outside-toplevel
import io
import json
import os

from django.utils import timezone

WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")
CLAUDE_MODEL = "claude-opus-4-8"

# Cache do modelo de transcrição: o load é caro e deve acontecer uma vez só.
_CACHE = {}


class TranscriptionUnavailable(RuntimeError):
    """faster-whisper não está instalado neste ambiente."""


class NoteGenerationUnavailable(RuntimeError):
    """ANTHROPIC_API_KEY não configurada."""


def _get_whisper_model():
    """Carrega o modelo uma vez por processo (o load é caro)."""
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
    """Transcreve um arquivo de áudio para texto (português)."""
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
    """Converte a transcrição crua numa nota clínica estruturada (dict)."""
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
    """Estilos de parágrafo do documento, nas cores do MedHelper."""
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
    """Gera o PDF do documento da consulta e devolve os bytes."""
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
    """Versão em texto puro da nota, para guardar em Appointment.transcript."""
    return "\n\n".join(
        f"{label}:\n{note.get(key) or 'Não relatado'}" for key, label in SECTIONS
    )
