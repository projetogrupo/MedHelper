"""Tests for the progress reporting of the appointment-document generation.

The pipeline itself is covered by test_ai_document.py; here the subject is
the job: the browser must get a percentage while it runs, the finished panel
when it ends, and the reason when it fails. External calls stay mocked.
"""
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core import ai, views

NOTA = {key: "conteudo" for key, _ in ai.SECTIONS}


@pytest.fixture(autouse=True)
def clear_job_cache():
    """Jobs live in the default (process-wide) cache — isolate the tests."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def audio():
    return SimpleUploadedFile("consulta.wav", b"fake-audio-bytes", "audio/wav")


@pytest.fixture
def own_appointment(appointment, doctor_client):
    return appointment


def post_via_htmx(client, appointment, audio):
    return client.post(
        reverse("attendance-transcribe", args=[appointment.id]),
        {"audio": audio},
        HTTP_HX_REQUEST="true",
    )


@pytest.mark.django_db
def test_htmx_upload_returns_progress_instead_of_redirecting(
    doctor_client, own_appointment, audio
):
    with patch.object(views.threading, "Thread") as thread:
        response = post_via_htmx(doctor_client, own_appointment, audio)

    html = response.content.decode()
    assert response.status_code == 200
    assert 'id="ai-panel"' in html
    assert "progress-fill" in html
    assert "Transcrevendo o áudio localmente" in html
    # The panel polls itself for updates.
    assert "hx-trigger" in html
    thread.return_value.start.assert_called_once()


@pytest.mark.django_db
def test_job_runs_the_pipeline_and_reports_done(own_appointment, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    audio_path = tmp_path / "a.wav"
    audio_path.write_bytes(b"x")

    with patch.object(ai, "transcribe_audio", return_value="transcricao"), \
         patch.object(ai, "build_medical_note", return_value=NOTA):
        views._run_document_job("job-1", own_appointment.id, str(audio_path))

    own_appointment.refresh_from_db()
    job = cache.get(views._job_key("job-1"))
    assert job["stage"] == "done"
    assert job["percent"] == 100
    assert own_appointment.transcript_pdf.name.endswith(".pdf")
    # The temporary upload is removed whatever happens.
    assert not audio_path.exists()


@pytest.mark.django_db
def test_job_records_the_failure_reason(own_appointment, tmp_path):
    audio_path = tmp_path / "a.wav"
    audio_path.write_bytes(b"x")

    with patch.object(
        ai, "transcribe_audio",
        side_effect=ai.NoteGenerationUnavailable("ANTHROPIC_API_KEY não configurada"),
    ):
        views._run_document_job("job-2", own_appointment.id, str(audio_path))

    job = cache.get(views._job_key("job-2"))
    assert job["stage"] == "error"
    assert "ANTHROPIC_API_KEY" in job["error"]
    assert not audio_path.exists()


@pytest.mark.django_db
def test_silent_audio_is_reported_as_an_error(own_appointment, tmp_path):
    audio_path = tmp_path / "a.wav"
    audio_path.write_bytes(b"x")
    with patch.object(ai, "transcribe_audio", return_value=""):
        views._run_document_job("job-3", own_appointment.id, str(audio_path))
    assert "extrair fala" in cache.get(views._job_key("job-3"))["error"]


@pytest.mark.django_db
def test_status_shows_the_running_percentage(doctor_client, own_appointment):
    views._set_job("job-4", stage="structuring", percent=74)
    html = doctor_client.get(
        reverse("attendance-transcribe-status", args=[own_appointment.id, "job-4"])
    ).content.decode()
    assert "74%" in html
    assert "Estruturando a nota clínica" in html
    # Transcription already happened, so its step is ticked off.
    assert "progress-step--done" in html


@pytest.mark.django_db
def test_status_returns_the_panel_when_finished(doctor_client, own_appointment):
    views._set_job("job-5", stage="done", percent=100)
    html = doctor_client.get(
        reverse("attendance-transcribe-status", args=[own_appointment.id, "job-5"])
    ).content.decode()
    assert "gerado com sucesso" in html
    # No polling attribute: the browser must stop asking.
    assert "hx-trigger" not in html


@pytest.mark.django_db
def test_status_surfaces_the_error_and_stops_polling(doctor_client, own_appointment):
    views._set_job("job-6", stage="error", percent=100, error="Falha X")
    html = doctor_client.get(
        reverse("attendance-transcribe-status", args=[own_appointment.id, "job-6"])
    ).content.decode()
    assert "Falha X" in html
    assert "hx-trigger" not in html


@pytest.mark.django_db
def test_unknown_job_falls_back_to_the_panel(doctor_client, own_appointment):
    """Cache entries expire; the panel must still render, not error out."""
    response = doctor_client.get(
        reverse("attendance-transcribe-status", args=[own_appointment.id, "gone"])
    )
    assert response.status_code == 200
    assert 'id="ai-panel"' in response.content.decode()


@pytest.mark.django_db
def test_status_is_refused_to_other_doctors(patient_client, appointment):
    response = patient_client.get(
        reverse("attendance-transcribe-status", args=[appointment.id, "job-7"])
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_progress_percentage_rises_through_the_pipeline(own_appointment, settings, tmp_path):
    """The bar must only ever move forward."""
    settings.MEDIA_ROOT = tmp_path
    seen = []

    def fake_transcribe(_path, on_progress=None):
        for ratio in (0.25, 0.5, 1.0):
            on_progress(ratio)
        return "transcricao"

    with patch.object(ai, "transcribe_audio", side_effect=fake_transcribe), \
         patch.object(ai, "build_medical_note", return_value=NOTA):
        views._build_document(
            own_appointment, str(tmp_path / "a.wav"),
            report=lambda stage, percent: seen.append((stage, percent)),
        )

    percentages = [percent for _stage, percent in seen]
    assert percentages == sorted(percentages)
    assert percentages[-1] == 100
    assert seen[-1][0] == "done"
    assert {stage for stage, _ in seen} == {
        "transcribing", "structuring", "rendering", "done",
    }


def test_transcribe_reports_progress_against_the_audio_duration():
    """The ratio comes from segment timestamps, not a guess."""
    class Segment:
        def __init__(self, end, text):
            self.end = end
            self.text = text

    class Info:
        duration = 20.0

    class Model:
        def transcribe(self, *_args, **_kwargs):
            return iter([Segment(5.0, "um"), Segment(20.0, "dois")]), Info()

    reported = []
    with patch.object(ai, "_get_whisper_model", return_value=Model()):
        text = ai.transcribe_audio("x.wav", on_progress=reported.append)

    assert text == "um dois"
    assert reported == [0.25, 1.0, 1.0]
