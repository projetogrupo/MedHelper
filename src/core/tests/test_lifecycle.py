import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from core.models import Appointment


@pytest.fixture
def past_appointment(patient, doctor):
    return Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=timezone.now() - datetime.timedelta(days=1),
        status=Appointment.STATUS_SCHEDULED,
    )


@pytest.fixture
def future_appointment(patient, doctor):
    return Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=timezone.now() + datetime.timedelta(days=3),
        status=Appointment.STATUS_SCHEDULED,
    )


@pytest.mark.django_db
def test_booking_form_has_no_reason_field(patient_client):
    html = patient_client.get(reverse("index")).content.decode()
    assert "Motivo" not in html


@pytest.mark.django_db
def test_doctor_completes_own_past_appointment(doctor_client, past_appointment):
    response = doctor_client.post(
        reverse("appointment-complete", args=[past_appointment.id])
    )
    past_appointment.refresh_from_db()
    assert response.status_code == 200
    assert past_appointment.status == "completed"


@pytest.mark.django_db
def test_future_appointment_cannot_be_completed(doctor_client, future_appointment):
    response = doctor_client.post(
        reverse("appointment-complete", args=[future_appointment.id])
    )
    future_appointment.refresh_from_db()
    assert response.status_code == 422
    assert future_appointment.status == "scheduled"


@pytest.mark.django_db
def test_patient_cannot_complete(patient_client, past_appointment):
    response = patient_client.post(
        reverse("appointment-complete", args=[past_appointment.id])
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_completes_any_past_appointment(admin_client, past_appointment):
    response = admin_client.post(
        reverse("appointment-complete", args=[past_appointment.id])
    )
    past_appointment.refresh_from_db()
    assert response.status_code == 200
    assert past_appointment.status == "completed"


@pytest.mark.django_db
def test_doctor_agenda_shows_complete_button_for_overdue(doctor_client, past_appointment):
    html = doctor_client.get(reverse("appointment-list")).content.decode()
    assert "Concluir" in html


@pytest.mark.django_db
def test_overdue_appointment_is_flagged(patient_client, past_appointment):
    html = patient_client.get(reverse("appointment-list")).content.decode()
    assert "Atrasada" in html


@pytest.mark.django_db
def test_completed_past_appointment_not_flagged(patient_client, past_appointment):
    past_appointment.status = Appointment.STATUS_COMPLETED
    past_appointment.save()
    html = patient_client.get(reverse("appointment-list")).content.decode()
    assert "Atrasada" not in html
