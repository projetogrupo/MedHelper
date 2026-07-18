import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse


@pytest.fixture
def anon_client():
    return Client()


@pytest.mark.django_db
def test_index_requires_login(anon_client):
    response = anon_client.get(reverse("index"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_appointment_list_requires_login(anon_client):
    response = anon_client.get(reverse("appointment-list"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_login_page_renders(anon_client):
    response = anon_client.get(reverse("login"))
    assert response.status_code == 200
    assert "Entrar" in response.content.decode()


@pytest.mark.django_db
def test_login_redirects_to_index(anon_client):
    User.objects.create_user("ana", password="segredo123")
    response = anon_client.post(
        reverse("login"), {"username": "ana", "password": "segredo123"}
    )
    assert response.status_code == 302
    assert response.url == reverse("index")


@pytest.mark.django_db
def test_login_rejects_bad_credentials(anon_client):
    User.objects.create_user("ana", password="segredo123")
    response = anon_client.post(
        reverse("login"), {"username": "ana", "password": "errada"}
    )
    assert response.status_code == 200
    assert "inválidos" in response.content.decode()


@pytest.mark.django_db
def test_logout_redirects_to_login(client):
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")
