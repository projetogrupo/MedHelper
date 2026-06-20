import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_create_doctor_valid(client):
    response = client.post(
        reverse("doctor-create"),
        {
            "first_name": "Carla",
            "last_name": "Dias",
            "specialty": "Dermatology",
            "email": "carla@example.com",
            "crm_number": "CRM-2002",
        },
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_create_doctor_duplicate_email(client, doctor):
    response = client.post(
        reverse("doctor-create"),
        {
            "first_name": "Diego",
            "last_name": "Reis",
            "specialty": "Neurology",
            "email": doctor.email,
            "crm_number": "CRM-3003",
        },
    )
    assert response.status_code == 422


@pytest.mark.django_db
def test_create_doctor_duplicate_crm(client, doctor):
    response = client.post(
        reverse("doctor-create"),
        {
            "first_name": "Elena",
            "last_name": "Matos",
            "specialty": "Pediatrics",
            "email": "elena@example.com",
            "crm_number": doctor.crm_number,
        },
    )
    assert response.status_code == 422


@pytest.mark.django_db
def test_create_doctor_missing_first_name(client):
    response = client.post(
        reverse("doctor-create"),
        {"last_name": "Costa", "specialty": "Cardiology"},
    )
    assert response.status_code == 422


@pytest.mark.django_db
def test_create_doctor_missing_specialty(client):
    response = client.post(
        reverse("doctor-create"),
        {"first_name": "Bruno", "last_name": "Costa"},
    )
    assert response.status_code == 422
