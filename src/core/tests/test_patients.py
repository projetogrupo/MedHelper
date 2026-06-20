import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_create_patient_valid(client):
    response = client.post(
        reverse("patient-create"),
        {
            "first_name": "Ana",
            "last_name": "Silva",
            "email": "ana@example.com",
            "phone": "11999990000",
            "address": "123 Main St",
        },
    )
    assert response.status_code == 201
    assert b"Ana" in response.content


@pytest.mark.django_db
def test_create_patient_missing_first_name(client):
    response = client.post(reverse("patient-create"), {"last_name": "Silva"})
    assert response.status_code == 422


@pytest.mark.django_db
def test_create_patient_missing_last_name(client):
    response = client.post(reverse("patient-create"), {"first_name": "Ana"})
    assert response.status_code == 422
