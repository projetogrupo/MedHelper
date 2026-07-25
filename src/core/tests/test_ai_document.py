"""Tests for the AI appointment document generation.

Transcription (faster-whisper) and the model call are mocked: CI must not
download models, hit the network or spend API credit.
"""
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core import ai

NOTA = {
    "queixa_principal": "Cefaleia há duas semanas.",
    "historia_doenca_atual": "Dor em pressão, bilateral, frontal.",
    "achados_exame": "PA 140x90 mmHg.",
    "hipotese_diagnostica": "Não relatado",
    "conduta": "Exames de sangue; manter losartana 50 mg.",
    "retorno": "Retorno em um mês.",
}


@pytest.fixture
def audio():
    return SimpleUploadedFile("consulta.wav", b"fake-audio-bytes", "audio/wav")


@pytest.fixture
def own_appointment(appointment, doctor_client):
    """Appointment owned by the doctor logged in via doctor_client."""
    return appointment


@pytest.mark.django_db
def test_generates_document(doctor_client, own_appointment, audio, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    with patch.object(ai, "transcribe_audio", return_value="transcricao crua"), \
         patch.object(ai, "build_medical_note", return_value=NOTA) as build:
        response = doctor_client.post(
            reverse("attendance-transcribe", args=[own_appointment.id]),
            {"audio": audio},
        )

    own_appointment.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("attendance", args=[own_appointment.id])
    build.assert_called_once_with("transcricao crua")
    assert own_appointment.transcript_pdf.name.endswith(".pdf")
    assert own_appointment.transcript_created_at is not None
    assert "Cefaleia há duas semanas." in own_appointment.transcript


@pytest.mark.django_db
def test_generated_pdf_is_a_real_pdf(doctor_client, own_appointment, audio, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    with patch.object(ai, "transcribe_audio", return_value="x"), \
         patch.object(ai, "build_medical_note", return_value=NOTA):
        doctor_client.post(
            reverse("attendance-transcribe", args=[own_appointment.id]),
            {"audio": audio},
        )
    own_appointment.refresh_from_db()
    with own_appointment.transcript_pdf.open("rb") as handle:
        assert handle.read(5) == b"%PDF-"


@pytest.mark.django_db
def test_patient_cannot_generate(patient_client, appointment, audio):
    response = patient_client.post(
        reverse("attendance-transcribe", args=[appointment.id]), {"audio": audio}
    )
    appointment.refresh_from_db()
    assert response.status_code == 403
    assert not appointment.transcript_pdf


@pytest.mark.django_db
def test_other_doctor_cannot_generate(admin_client, appointment, audio):
    """The admin is not the appointment's doctor — own_attendance refuses."""
    response = admin_client.post(
        reverse("attendance-transcribe", args=[appointment.id]), {"audio": audio}
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_missing_audio_is_rejected(doctor_client, own_appointment):
    response = doctor_client.post(
        reverse("attendance-transcribe", args=[own_appointment.id]), {}
    )
    own_appointment.refresh_from_db()
    assert response.status_code == 302
    assert not own_appointment.transcript_pdf


@pytest.mark.django_db
def test_empty_transcription_does_not_save(doctor_client, own_appointment, audio):
    """Audio with no recognizable speech must not produce a document."""
    with patch.object(ai, "transcribe_audio", return_value=""):
        response = doctor_client.post(
            reverse("attendance-transcribe", args=[own_appointment.id]),
            {"audio": audio},
        )
    own_appointment.refresh_from_db()
    assert response.status_code == 302
    assert not own_appointment.transcript_pdf


@pytest.mark.django_db
def test_missing_api_key_is_reported(doctor_client, own_appointment, audio):
    with patch.object(ai, "transcribe_audio", return_value="texto"), \
         patch.object(
             ai, "build_medical_note",
             side_effect=ai.NoteGenerationUnavailable("ANTHROPIC_API_KEY não configurada"),
         ):
        response = doctor_client.post(
            reverse("attendance-transcribe", args=[own_appointment.id]),
            {"audio": audio},
        )
    own_appointment.refresh_from_db()
    assert response.status_code == 302
    assert not own_appointment.transcript_pdf


@pytest.mark.django_db
def test_api_error_does_not_break_the_page(doctor_client, own_appointment, audio):
    with patch.object(ai, "transcribe_audio", return_value="texto"), \
         patch.object(ai, "build_medical_note", side_effect=RuntimeError("timeout")):
        response = doctor_client.post(
            reverse("attendance-transcribe", args=[own_appointment.id]),
            {"audio": audio},
        )
    own_appointment.refresh_from_db()
    assert response.status_code == 302
    assert not own_appointment.transcript_pdf


@pytest.mark.django_db
def test_attendance_screen_shows_generate_form(doctor_client, own_appointment):
    own_appointment.status = "in_progress"
    own_appointment.save()
    html = doctor_client.get(
        reverse("attendance", args=[own_appointment.id])
    ).content.decode()
    assert "Documento da consulta (IA)" in html
    assert reverse("attendance-transcribe", args=[own_appointment.id]) in html


@pytest.mark.django_db
def test_note_to_text_has_all_sections(appointment):
    texto = ai.note_to_text(NOTA)
    for _key, label in ai.SECTIONS:
        assert label in texto


@pytest.mark.django_db
def test_note_to_text_fills_missing_section(appointment):
    texto = ai.note_to_text({"queixa_principal": "Dor"})
    assert "Não relatado" in texto


@pytest.mark.django_db
def test_render_pdf_returns_pdf_bytes(appointment):
    pdf = ai.render_note_pdf(appointment, NOTA)
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 500


def test_build_medical_note_without_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ai.NoteGenerationUnavailable):
        ai.build_medical_note("transcricao", api_key=None)
