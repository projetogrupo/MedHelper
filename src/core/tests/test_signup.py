import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from core.models import Doctor, Patient


@pytest.fixture
def anon_client():
    return Client()


@pytest.mark.django_db
def test_signup_choice_page_renders(anon_client):
    response = anon_client.get(reverse("signup"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "paciente" in html.lower()
    assert "médico" in html.lower()


@pytest.mark.django_db
def test_patient_signup_creates_linked_profile(anon_client):
    response = anon_client.post(
        reverse("signup-patient"),
        {
            "username": "ana",
            "password1": "medhelper-forte-1",
            "password2": "medhelper-forte-1",
            "first_name": "Ana",
            "last_name": "Silva",
        },
    )
    assert response.status_code == 302
    user = User.objects.get(username="ana")
    assert user.patient.first_name == "Ana"


@pytest.mark.django_db
def test_patient_signup_logs_user_in(anon_client):
    anon_client.post(
        reverse("signup-patient"),
        {
            "username": "ana",
            "password1": "medhelper-forte-1",
            "password2": "medhelper-forte-1",
            "first_name": "Ana",
            "last_name": "Silva",
        },
    )
    response = anon_client.get(reverse("index"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_doctor_signup_creates_linked_profile(anon_client):
    response = anon_client.post(
        reverse("signup-doctor"),
        {
            "username": "drb",
            "password1": "medhelper-forte-1",
            "password2": "medhelper-forte-1",
            "first_name": "Bruno",
            "last_name": "Costa",
            "specialty": "Cardiologia",
            "crm_number": "CRM-1234",
        },
    )
    assert response.status_code == 302
    user = User.objects.get(username="drb")
    assert user.doctor.specialty == "Cardiologia"


@pytest.mark.django_db
def test_doctor_signup_lands_on_appointment_list(anon_client):
    anon_client.post(
        reverse("signup-doctor"),
        {
            "username": "drb",
            "password1": "medhelper-forte-1",
            "password2": "medhelper-forte-1",
            "first_name": "Bruno",
            "last_name": "Costa",
            "specialty": "Cardiologia",
        },
    )
    response = anon_client.get(reverse("index"))
    assert response.status_code == 302
    assert response.url == reverse("appointment-list")


@pytest.mark.django_db
def test_signup_password_mismatch_creates_nothing(anon_client):
    response = anon_client.post(
        reverse("signup-patient"),
        {
            "username": "ana",
            "password1": "medhelper-forte-1",
            "password2": "diferente-2",
            "first_name": "Ana",
            "last_name": "Silva",
        },
    )
    assert response.status_code == 200
    assert not User.objects.filter(username="ana").exists()
    assert not Patient.objects.exists()


@pytest.mark.django_db
def test_login_page_links_to_signup(anon_client):
    html = anon_client.get(reverse("login")).content.decode()
    assert reverse("signup") in html
