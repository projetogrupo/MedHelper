import pytest
from django.utils import timezone

from core.models import Appointment, Doctor, Patient


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
