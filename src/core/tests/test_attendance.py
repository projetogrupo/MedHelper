import datetime

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.models import Appointment, User


@pytest.fixture
def today_appointment(patient, doctor):
    return Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=timezone.now() - datetime.timedelta(hours=1),
        status=Appointment.STATUS_SCHEDULED,
    )


@pytest.fixture
def future_appointment(patient, doctor):
    return Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=timezone.now() + datetime.timedelta(days=5),
        status=Appointment.STATUS_SCHEDULED,
    )


@pytest.mark.django_db
def test_doctor_starts_todays_appointment(doctor_client, today_appointment):
    response = doctor_client.post(
        reverse("appointment-start", args=[today_appointment.id])
    )
    today_appointment.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("attendance", args=[today_appointment.id])
    assert today_appointment.status == "in_progress"


@pytest.mark.django_db
def test_future_appointment_cannot_start(doctor_client, future_appointment):
    response = doctor_client.post(
        reverse("appointment-start", args=[future_appointment.id])
    )
    future_appointment.refresh_from_db()
    assert response.status_code == 422
    assert future_appointment.status == "scheduled"


@pytest.mark.django_db
def test_patient_cannot_start(patient_client, today_appointment):
    response = patient_client.post(
        reverse("appointment-start", args=[today_appointment.id])
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_other_doctor_cannot_start(today_appointment):
    from core.models import Doctor
    other = Doctor.objects.create(
        first_name="Rita", last_name="Nunes", specialty="Ortopedia",
        email="rita@example.com", crm_number="CRM-9999",
    )
    user = User.objects.create_user("rita@example.com", password="x")
    other.user = user
    other.save()
    logged = Client()
    logged.force_login(user)
    response = logged.post(reverse("appointment-start", args=[today_appointment.id]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_agenda_shows_start_without_motivo(doctor_client, today_appointment):
    html = doctor_client.get(reverse("appointment-list")).content.decode()
    assert "Iniciar" in html
    assert "Motivo" not in html


@pytest.mark.django_db
def test_agenda_shows_in_progress_badge(doctor_client, today_appointment):
    today_appointment.status = Appointment.STATUS_IN_PROGRESS
    today_appointment.save()
    html = doctor_client.get(reverse("appointment-list")).content.decode()
    assert "Em andamento" in html
    assert "Abrir" in html


@pytest.fixture
def open_appointment(today_appointment):
    today_appointment.status = Appointment.STATUS_IN_PROGRESS
    today_appointment.save()
    return today_appointment


@pytest.mark.django_db
def test_attendance_screen_renders(doctor_client, open_appointment):
    html = doctor_client.get(
        reverse("attendance", args=[open_appointment.id])
    ).content.decode()
    assert "Ana" in html
    assert "Anotações" in html
    assert "Concluir" in html


@pytest.mark.django_db
def test_attendance_blocked_for_scheduled(doctor_client, today_appointment):
    response = doctor_client.get(reverse("attendance", args=[today_appointment.id]))
    assert response.status_code == 302
    assert response.url == reverse("appointment-list")


@pytest.mark.django_db
def test_attendance_forbidden_for_patient(patient_client, open_appointment):
    response = patient_client.get(reverse("attendance", args=[open_appointment.id]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_notes_are_saved(doctor_client, open_appointment):
    response = doctor_client.post(
        reverse("attendance-notes", args=[open_appointment.id]),
        {"notes": "Paciente estável."},
    )
    open_appointment.refresh_from_db()
    assert response.status_code == 302
    assert open_appointment.notes == "Paciente estável."


@pytest.mark.django_db
def test_document_upload_and_delete(doctor_client, open_appointment, settings, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile

    settings.MEDIA_ROOT = tmp_path
    doctor_client.post(
        reverse("attendance-doc-add", args=[open_appointment.id]),
        {"file": SimpleUploadedFile("exame.txt", b"resultado")},
    )
    document = open_appointment.documents.get()
    html = doctor_client.get(
        reverse("attendance", args=[open_appointment.id])
    ).content.decode()
    assert "exame" in html
    doctor_client.post(reverse("attendance-doc-delete", args=[document.id]))
    assert not open_appointment.documents.exists()


@pytest.mark.django_db
def test_attendance_complete(doctor_client, open_appointment):
    response = doctor_client.post(
        reverse("attendance-complete", args=[open_appointment.id])
    )
    open_appointment.refresh_from_db()
    assert response.status_code == 302
    assert open_appointment.status == "completed"


@pytest.mark.django_db
def test_patient_history_page_for_attending_doctor(doctor_client, open_appointment, patient, doctor):
    Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=timezone.now() - datetime.timedelta(days=30),
        status=Appointment.STATUS_COMPLETED,
        notes="Histórico antigo",
    )
    html = doctor_client.get(
        reverse("patient-history", args=[patient.id])
    ).content.decode()
    assert "Ana" in html
    assert "Histórico antigo" in html


@pytest.mark.django_db
def test_patient_history_forbidden_for_unrelated_doctor(patient):
    from core.models import Doctor
    other = Doctor.objects.create(
        first_name="Rita", last_name="Nunes", specialty="Ortopedia",
        email="rita@example.com", crm_number="CRM-9999",
    )
    user = User.objects.create_user("rita@example.com", password="x")
    other.user = user
    other.save()
    logged = Client()
    logged.force_login(user)
    response = logged.get(reverse("patient-history", args=[patient.id]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_patient_history_forbidden_for_patients(patient_client, patient):
    response = patient_client.get(reverse("patient-history", args=[patient.id]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_patient_history_allowed_for_admin(admin_client, patient):
    response = admin_client.get(reverse("patient-history", args=[patient.id]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_attendance_links_to_full_history(doctor_client, open_appointment, patient):
    html = doctor_client.get(
        reverse("attendance", args=[open_appointment.id])
    ).content.decode()
    assert reverse("patient-history", args=[patient.id]) in html


@pytest.mark.django_db
def test_attendance_shows_patient_history(doctor_client, open_appointment, patient, doctor):
    Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=timezone.now() - datetime.timedelta(days=30),
        status=Appointment.STATUS_COMPLETED,
        notes="Histórico antigo",
    )
    html = doctor_client.get(
        reverse("attendance", args=[open_appointment.id])
    ).content.decode()
    assert "Histórico antigo" in html
