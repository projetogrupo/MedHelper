"""Tests for the closed specialty list.

Specialty used to be free text, so two doctors in the same field could be
filed under "Cardiologia" and "cardiologia" and never appear in the same
booking filter. It is now a fixed vocabulary.
"""
import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from core.forms import DoctorProfileForm, DoctorSignupForm
from core.models import Doctor, MedicalSpecialty


def test_list_covers_the_most_common_specialties():
    values = set(MedicalSpecialty.values)
    assert len(values) == 20
    # The seven that hold half of Brazil's specialists must all be offered.
    assert {
        "Clínica Médica", "Pediatria", "Cirurgia Geral",
        "Ginecologia e Obstetrícia", "Anestesiologia", "Cardiologia",
        "Ortopedia e Traumatologia",
    } <= values


@pytest.mark.django_db
def test_model_rejects_a_specialty_outside_the_list(doctor):
    doctor.specialty = "Bruxaria"
    with pytest.raises(ValidationError):
        doctor.full_clean()


@pytest.mark.django_db
def test_model_accepts_a_listed_specialty(doctor):
    doctor.specialty = MedicalSpecialty.NEUROLOGIA
    doctor.full_clean()  # must not raise


@pytest.mark.django_db
def test_signup_form_offers_the_list_and_refuses_free_text():
    form = DoctorSignupForm()
    rendered = str(form["specialty"])
    assert "<select" in rendered
    assert "Otorrinolaringologia" in rendered

    bound = DoctorSignupForm(data={
        "email": "novo@example.com",
        "password1": "senha-bem-longa-123",
        "password2": "senha-bem-longa-123",
        "first_name": "Ana",
        "last_name": "Reis",
        "specialty": "Especialidade Inventada",
    })
    assert not bound.is_valid()
    assert "specialty" in bound.errors


@pytest.mark.django_db
def test_signup_form_accepts_a_listed_specialty():
    form = DoctorSignupForm(data={
        "email": "nova@example.com",
        "password1": "senha-bem-longa-123",
        "password2": "senha-bem-longa-123",
        "first_name": "Ana",
        "last_name": "Reis",
        "specialty": MedicalSpecialty.PSIQUIATRIA,
    })
    assert form.is_valid(), form.errors
    form.save()
    assert Doctor.objects.get(email="nova@example.com").specialty == "Psiquiatria"


@pytest.mark.django_db
def test_profile_form_is_a_dropdown_too(doctor):
    """The specialty must not be editable as free text after signup either."""
    assert "<select" in str(DoctorProfileForm(instance=doctor)["specialty"])
    form = DoctorProfileForm(
        instance=doctor,
        data={
            "first_name": doctor.first_name,
            "last_name": doctor.last_name,
            "specialty": "Qualquer Coisa",
            "email": doctor.email,
            "crm_number": doctor.crm_number or "",
            "phone": "",
        },
    )
    assert not form.is_valid()
    assert "specialty" in form.errors


@pytest.mark.django_db
def test_signup_screen_renders_the_dropdown(client):
    html = client.get(reverse("signup-doctor")).content.decode()
    assert "Clínica Médica" in html
    assert "Medicina de Família e Comunidade" in html
