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
