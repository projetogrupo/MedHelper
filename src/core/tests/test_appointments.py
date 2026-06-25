import pytest
from django.urls import reverse
from urllib.parse import urlencode


@pytest.mark.django_db
def test_create_appointment_valid(client, patient, doctor):
    response = client.post(
        reverse("appointment-create"),
        {
            "patient": patient.id,
            "doctor": doctor.id,
            "appointment_date": "2026-07-01 10:00",
            "reason": "Initial visit",
            "status": "scheduled",
        },
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_create_appointment_missing_date(client, patient, doctor):
    response = client.post(
        reverse("appointment-create"),
        {
            "patient": patient.id,
            "doctor": doctor.id,
            "status": "scheduled",
        },
    )
    assert response.status_code == 422


@pytest.mark.django_db
def test_list_appointments_no_filter(client, appointment):
    response = client.get(reverse("appointment-list"))
    assert response.status_code == 200
    assert b"Ana" in response.content


@pytest.mark.django_db
def test_list_appointments_filter_match(client, appointment):
    response = client.get(reverse("appointment-list"), {"q": "Ana"})
    assert response.status_code == 200
    assert b"Ana" in response.content


@pytest.mark.django_db
def test_list_appointments_filter_no_match(client, appointment):
    response = client.get(reverse("appointment-list"), {"q": "Zzz"})
    assert response.status_code == 200
    assert b"No appointments found." in response.content


@pytest.mark.django_db
def test_list_appointments_whitespace_query(client, appointment):
    response = client.get(reverse("appointment-list"), {"q": "   "})
    assert response.status_code == 200
    assert b"Ana" in response.content


@pytest.mark.django_db
def test_update_appointment_valid(client, appointment):
    payload = urlencode(
        {
            "patient": appointment.patient_id,
            "doctor": appointment.doctor_id,
            "appointment_date": "2026-08-15 14:30",
            "reason": "Follow-up",
            "status": "completed",
        }
    )
    response = client.put(
        reverse("appointment-update", args=[appointment.id]),
        data=payload,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 200
    assert b"Follow-up" in response.content


@pytest.mark.django_db
def test_update_appointment_invalid(client, appointment):
    payload = urlencode(
        {
            "patient": appointment.patient_id,
            "doctor": appointment.doctor_id,
            "appointment_date": "not-a-date",
            "status": "scheduled",
        }
    )
    response = client.put(
        reverse("appointment-update", args=[appointment.id]),
        data=payload,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 422
    assert b"Checkup" in response.content
    assert b"Invalid input" in response.content


@pytest.mark.django_db
def test_update_appointment_not_found(client):
    payload = urlencode({"appointment_date": "2026-08-15 14:30", "status": "scheduled"})
    response = client.put(
        reverse("appointment-update", args=[999999]),
        data=payload,
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_appointment_existing(client, appointment):
    response = client.delete(reverse("appointment-delete", args=[appointment.id]))
    assert response.status_code == 200
    assert response.content == b""


@pytest.mark.django_db
def test_delete_appointment_not_found(client):
    response = client.delete(reverse("appointment-delete", args=[999999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_list_appointments_renders_delete_control(client, appointment):
    response = client.get(reverse("appointment-list"))
    delete_url = reverse("appointment-delete", args=[appointment.id])
    assert response.status_code == 200
    assert f'hx-delete="{delete_url}"'.encode() in response.content


@pytest.mark.django_db
def test_list_appointments_null_patient(client, appointment):
    appointment.patient = None
    appointment.save()
    response = client.get(reverse("appointment-list"))
    assert response.status_code == 200
    assert b"(no patient)" in response.content
