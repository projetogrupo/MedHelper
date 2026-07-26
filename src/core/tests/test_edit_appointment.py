import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_admin_get_edit_form(client, appointment):
    """GET on appointment-update returns the inline edit form (not a 405)."""
    response = client.get(reverse("appointment-update", args=[appointment.id]))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Editar consulta" in html
    # The form must submit back via hx-put so saving still works.
    assert "hx-put" in html


@pytest.mark.django_db
def test_doctor_cannot_get_edit_form(doctor_client, appointment):
    response = doctor_client.get(reverse("appointment-update", args=[appointment.id]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_patient_cannot_get_edit_form(patient_client, appointment):
    response = patient_client.get(reverse("appointment-update", args=[appointment.id]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_edit_form_get_then_put_round_trip(client, appointment):
    """The Editar flow end to end: GET the form, then PUT the changes."""
    from urllib.parse import urlencode

    assert client.get(reverse("appointment-update", args=[appointment.id])).status_code == 200
    payload = urlencode({
        "patient": appointment.patient_id,
        "doctor": appointment.doctor_id,
        "appointment_date": "2026-08-15 14:30",
        "reason": "Retorno",
        "status": "scheduled",
    })
    response = client.put(
        reverse("appointment-update", args=[appointment.id]),
        data=payload,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Retorno" in response.content
