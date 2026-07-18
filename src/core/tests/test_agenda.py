import pytest

from core.models import Doctor


@pytest.mark.django_db
def test_appointment_duration_defaults_to_30(doctor):
    assert doctor.appointment_duration == 30
