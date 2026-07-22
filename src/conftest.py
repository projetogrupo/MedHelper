import pytest
from core.models import Appointment, Doctor, Patient, User
from django.test import Client
from django.utils import timezone



@pytest.fixture
def client(db):
    user = User.objects.create_superuser("tester@example.com", "x")
    logged_client = Client()
    logged_client.force_login(user)
    return logged_client


@pytest.fixture
def admin_client(db):
    user = User.objects.create_superuser("boss@example.com", "x")
    logged = Client()
    logged.force_login(user)
    return logged


@pytest.fixture
def doctor_client(doctor):
    user = User.objects.create_user("dra@example.com", password="x")
    doctor.user = user
    doctor.save()
    logged = Client()
    logged.force_login(user)
    return logged


@pytest.fixture
def patient_client(patient):
    user = User.objects.create_user("ana@example.com", password="x")
    patient.user = user
    patient.save()
    logged = Client()
    logged.force_login(user)
    return logged


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
