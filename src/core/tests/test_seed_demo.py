"""Tests for the seed_demo command.

The Docker entrypoint runs it on every container start, so the important
properties are: it produces a usable app from an empty database, and running
it again never duplicates or fails.
"""
import datetime

import pytest
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from core.models import Doctor, Patient, User, WeeklySlot


@pytest.mark.django_db
def test_creates_accounts_and_availability():
    call_command("seed_demo", verbosity=0)
    assert User.objects.filter(is_superuser=True).exists()
    assert Doctor.objects.count() == 2
    assert Patient.objects.count() == 2
    assert WeeklySlot.objects.exists()


@pytest.mark.django_db
def test_is_idempotent():
    call_command("seed_demo", verbosity=0)
    counts = (User.objects.count(), Doctor.objects.count(), WeeklySlot.objects.count())
    call_command("seed_demo", verbosity=0)
    assert (User.objects.count(), Doctor.objects.count(), WeeklySlot.objects.count()) == counts


@pytest.mark.django_db
def test_skips_when_database_already_has_users(patient):
    User.objects.create_user("someone@example.com", password="x")
    call_command("seed_demo", verbosity=0)
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_seeded_doctors_have_bookable_slots():
    """A fresh install must offer slots, otherwise booking cannot be demoed."""
    call_command("seed_demo", verbosity=0)
    doctor = Doctor.objects.first()
    today = datetime.date.today()
    next_monday = today + datetime.timedelta(days=(7 - today.weekday()) % 7 or 7)
    assert doctor.available_slots(next_monday)


@pytest.mark.django_db
def test_seeded_accounts_can_log_in():
    call_command("seed_demo", verbosity=0)
    # Plain Client: the project's `client` fixture pre-creates a superuser,
    # which would make seed_demo skip.
    assert Client().login(username="ana@medhelper.local", password="medhelper123")


@pytest.mark.django_db
def test_seeded_patient_reaches_the_booking_screen():
    call_command("seed_demo", verbosity=0)
    browser = Client()
    browser.login(username="ana@medhelper.local", password="medhelper123")
    response = browser.get(reverse("index"))
    assert response.status_code == 200
    assert "Cardiologia" in response.content.decode()


@pytest.mark.django_db
def test_password_can_be_overridden():
    call_command("seed_demo", "--password", "outra-senha", verbosity=0)
    user = User.objects.get(email="ana@medhelper.local")
    assert user.check_password("outra-senha")
