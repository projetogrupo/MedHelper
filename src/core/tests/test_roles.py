import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.models import Appointment, Doctor, Patient


@pytest.fixture
def other_appointment(db):
    other_patient = Patient.objects.create(first_name="Zeca", last_name="Moura")
    other_doctor = Doctor.objects.create(
        first_name="Rita", last_name="Nunes", specialty="Ortopedia",
        email="rita@example.com", crm_number="CRM-9999",
    )
    return Appointment.objects.create(
        patient=other_patient,
        doctor=other_doctor,
        appointment_date=timezone.now(),
        reason="Alheia",
        status=Appointment.STATUS_SCHEDULED,
    )


@pytest.mark.django_db
def test_admin_sees_all_appointments(admin_client, appointment, other_appointment):
    html = admin_client.get(reverse("appointment-list")).content.decode()
    assert "Checkup" in html
    assert "Alheia" in html


@pytest.mark.django_db
def test_doctor_sees_only_own_appointments(doctor_client, appointment, other_appointment):
    html = doctor_client.get(reverse("appointment-list")).content.decode()
    assert "Checkup" in html
    assert "Alheia" not in html
    assert "Excluir" not in html


@pytest.mark.django_db
def test_patient_sees_only_own_appointments(patient_client, appointment, other_appointment):
    html = patient_client.get(reverse("appointment-list")).content.decode()
    assert "Checkup" in html
    assert "Alheia" not in html
    assert "Excluir" not in html


@pytest.mark.django_db
def test_doctor_cannot_update_appointment(doctor_client, appointment):
    response = doctor_client.put(
        reverse("appointment-update", args=[appointment.id]), data="reason=x"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_patient_cannot_update_appointment(patient_client, appointment):
    response = patient_client.put(
        reverse("appointment-update", args=[appointment.id]), data="reason=x"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_doctor_index_redirects_to_list(doctor_client):
    response = doctor_client.get(reverse("index"))
    assert response.status_code == 302
    assert response.url == reverse("appointment-list")


@pytest.mark.django_db
def test_patient_books_only_for_self(patient_client, patient, doctor, other_appointment):
    response = patient_client.post(
        reverse("appointment-create"),
        {
            "patient": other_appointment.patient.id,
            "doctor": doctor.id,
            "appointment_date": "2026-09-01T10:00",
            "status": "scheduled",
            "reason": "Consulta minha",
        },
    )
    assert response.status_code == 201
    created = Appointment.objects.get(reason="Consulta minha")
    assert created.patient == patient


@pytest.mark.django_db
def test_doctor_cannot_delete_appointment(doctor_client, appointment):
    response = doctor_client.delete(
        reverse("appointment-delete", args=[appointment.id])
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_patient_cannot_delete_appointment(patient_client, appointment):
    response = patient_client.delete(
        reverse("appointment-delete", args=[appointment.id])
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_patient_cancels_own_appointment(patient_client, appointment):
    response = patient_client.post(
        reverse("appointment-cancel", args=[appointment.id])
    )
    appointment.refresh_from_db()
    assert response.status_code == 200
    assert appointment.status == "cancelled"


@pytest.mark.django_db
def test_patient_cannot_cancel_others_appointment(patient_client, other_appointment):
    response = patient_client.post(
        reverse("appointment-cancel", args=[other_appointment.id])
    )
    other_appointment.refresh_from_db()
    assert response.status_code == 403
    assert other_appointment.status == "scheduled"


@pytest.mark.django_db
def test_doctor_nav_has_no_booking_link(doctor_client):
    html = doctor_client.get(reverse("appointment-list")).content.decode()
    assert "Agendar" not in html


@pytest.mark.django_db
def test_patient_nav_has_booking_link(patient_client):
    html = patient_client.get(reverse("appointment-list")).content.decode()
    assert "Agendar" in html
