import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from core.models import Appointment


@pytest.fixture
def future_appointment(patient, doctor):
    return Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=timezone.now() + datetime.timedelta(days=3),
        reason="Retorno",
        status=Appointment.STATUS_SCHEDULED,
    )


@pytest.mark.django_db
def test_patient_screen_shows_sections_without_admin_actions(patient_client, appointment):
    html = patient_client.get(reverse("appointment-list")).content.decode()
    assert "Minhas consultas" in html
    assert "Próximas" in html
    assert "Anteriores" in html
    assert "Bruno Costa" in html
    assert "Editar" not in html
    assert "Excluir" not in html


@pytest.mark.django_db
def test_patient_upcoming_appointment_has_cancel(patient_client, future_appointment):
    html = patient_client.get(reverse("appointment-list")).content.decode()
    assert "Cancelar" in html


@pytest.mark.django_db
def test_patient_cancel_returns_patient_partial(patient_client, future_appointment):
    response = patient_client.post(
        reverse("appointment-cancel", args=[future_appointment.id])
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "Cancelada" in html
    assert "Excluir" not in html


@pytest.mark.django_db
def test_doctor_agenda_shows_patient_without_doctor_column(doctor_client, appointment):
    html = doctor_client.get(reverse("appointment-list")).content.decode()
    assert "Minha agenda" in html
    assert "Ana" in html
    assert "Paciente" in html
    assert "Médico" not in html
    assert "Excluir" not in html


@pytest.mark.django_db
def test_doctor_agenda_search_no_match(doctor_client, appointment):
    response = doctor_client.get(reverse("appointment-list"), {"q": "Zzz"})
    assert "Nenhuma consulta encontrada.".encode() in response.content
