"""Tests for the specialty guidance chat.

The model call is mocked: CI never hits the network or spends credit.
"""
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from core import ai


@pytest.mark.django_db
def test_page_renders_for_patient(patient_client):
    response = patient_client.get(reverse("specialty-chat"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Qual especialista procurar?" in html
    assert "Olá!" in html  # static greeting (no API cost)


@pytest.mark.django_db
def test_page_links_back_to_booking(patient_client):
    html = patient_client.get(reverse("specialty-chat")).content.decode()
    assert "Voltar ao agendamento" in html
    assert f'href="{reverse("index")}"' in html


@pytest.mark.django_db
def test_page_forbidden_for_doctor(doctor_client):
    assert doctor_client.get(reverse("specialty-chat")).status_code == 403


@pytest.mark.django_db
def test_page_forbidden_for_admin(admin_client):
    assert admin_client.get(reverse("specialty-chat")).status_code == 403


@pytest.mark.django_db
def test_page_requires_login(db):
    response = Client().get(reverse("specialty-chat"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_send_shows_user_message_and_reply(patient_client):
    with patch.object(
        ai, "specialty_chat_reply", return_value="Procure um cardiologista."
    ) as mock_reply:
        response = patient_client.post(
            reverse("specialty-chat-send"),
            {"message": "Dor no peito ao subir escada"},
        )
    html = response.content.decode()
    assert response.status_code == 200
    assert "Dor no peito ao subir escada" in html
    assert "Procure um cardiologista." in html
    history = mock_reply.call_args.args[0]
    assert history[-1] == {"role": "user", "content": "Dor no peito ao subir escada"}


@pytest.mark.django_db
def test_history_persists_between_messages(patient_client):
    with patch.object(ai, "specialty_chat_reply", side_effect=["R1", "R2"]) as mock_reply:
        patient_client.post(reverse("specialty-chat-send"), {"message": "Oi"})
        response = patient_client.post(
            reverse("specialty-chat-send"), {"message": "Dor de cabeça"}
        )
    html = response.content.decode()
    for expected in ("Oi", "R1", "Dor de cabeça", "R2"):
        assert expected in html
    # the second turn sends the accumulated conversation to the model
    second_call_history = mock_reply.call_args.args[0]
    assert len(second_call_history) == 3


@pytest.mark.django_db
def test_clinic_specialties_passed_to_model(patient_client, doctor):
    with patch.object(ai, "specialty_chat_reply", return_value="ok") as mock_reply:
        patient_client.post(reverse("specialty-chat-send"), {"message": "x"})
    assert doctor.specialty in mock_reply.call_args.args[1]


@pytest.mark.django_db
def test_blank_message_does_not_call_model(patient_client):
    with patch.object(ai, "specialty_chat_reply") as mock_reply:
        response = patient_client.post(reverse("specialty-chat-send"), {"message": "   "})
    assert response.status_code == 200
    mock_reply.assert_not_called()


@pytest.mark.django_db
def test_send_forbidden_for_doctor(doctor_client):
    with patch.object(ai, "specialty_chat_reply") as mock_reply:
        response = doctor_client.post(reverse("specialty-chat-send"), {"message": "Oi"})
    assert response.status_code == 403
    mock_reply.assert_not_called()


@pytest.mark.django_db
def test_missing_key_shows_error(patient_client):
    with patch.object(
        ai, "specialty_chat_reply",
        side_effect=ai.AssistantUnavailable("ANTHROPIC_API_KEY não configurada no .env"),
    ):
        response = patient_client.post(reverse("specialty-chat-send"), {"message": "Oi"})
    assert "ANTHROPIC_API_KEY" in response.content.decode()


@pytest.mark.django_db
def test_api_error_shows_friendly_message(patient_client):
    with patch.object(ai, "specialty_chat_reply", side_effect=RuntimeError("boom")):
        response = patient_client.post(reverse("specialty-chat-send"), {"message": "Oi"})
    html = response.content.decode()
    assert response.status_code == 200
    assert "indisponível" in html
    assert "boom" not in html  # internal error must not leak


@pytest.mark.django_db
def test_reset_clears_history(patient_client):
    with patch.object(ai, "specialty_chat_reply", return_value="R1"):
        patient_client.post(reverse("specialty-chat-send"), {"message": "Oi"})
    response = patient_client.post(reverse("specialty-chat-reset"))
    html = response.content.decode()
    assert "R1" not in html
    assert "Olá!" in html


@pytest.mark.django_db
def test_nav_shows_link_for_patient_only(patient_client, doctor_client):
    assert "Orientação" in patient_client.get(reverse("appointment-list")).content.decode()
    assert "Orientação" not in doctor_client.get(reverse("appointment-list")).content.decode()


def test_reply_without_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ai.AssistantUnavailable):
        ai.specialty_chat_reply([{"role": "user", "content": "oi"}])
