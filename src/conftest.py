import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from core.models import Appointment, Doctor, Patient


@pytest.fixture
def client(db):
    user = User.objects.create_user("tester", password="x")
    logged_client = Client()
    logged_client.force_login(user)
    return logged_client


@pytest.fixture
def patient(db):
    return Patient.objects.create(first_name="Ana", last_name="Silva")


@pytest.fixture
def doctor(db):
    return Doctor.objects.create(
        first_name="Bruno",
        last_name="Costa",
        specialty="Cardiology",
        email="bruno@example.com",
        crm_number="CRM-0001",
    )


@pytest.fixture
def appointment(db, patient, doctor):
    return Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=timezone.now(),
        reason="Checkup",
        status=Appointment.STATUS_SCHEDULED,
    )
