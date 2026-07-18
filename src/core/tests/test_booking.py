import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from core.models import Appointment, Patient, WeeklySlot

MONDAY = datetime.date(2026, 7, 27)


@pytest.fixture
def monday_slots(doctor):
    WeeklySlot.objects.create(doctor=doctor, weekday=0, start_time=datetime.time(8, 0))
    WeeklySlot.objects.create(doctor=doctor, weekday=0, start_time=datetime.time(8, 30))
    return doctor


def book(doctor, when, **kwargs):
    return Appointment.objects.create(
        doctor=doctor,
        appointment_date=timezone.make_aware(when),
        **kwargs,
    )


@pytest.mark.django_db
def test_available_slots_excludes_taken(monday_slots, patient):
    book(monday_slots, datetime.datetime(2026, 7, 27, 8, 0), patient=patient)
    assert monday_slots.available_slots(MONDAY) == [datetime.time(8, 30)]


@pytest.mark.django_db
def test_cancelled_appointment_frees_slot(monday_slots, patient):
    book(
        monday_slots,
        datetime.datetime(2026, 7, 27, 8, 0),
        patient=patient,
        status=Appointment.STATUS_CANCELLED,
    )
    assert monday_slots.available_slots(MONDAY) == [
        datetime.time(8, 0),
        datetime.time(8, 30),
    ]


@pytest.mark.django_db
def test_slots_endpoint_lists_free_times(patient_client, monday_slots):
    response = patient_client.get(
        reverse("booking-slots"), {"doctor": monday_slots.id, "date": "2026-07-27"}
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert "08:00" in html
    assert "08:30" in html


@pytest.mark.django_db
def test_slots_endpoint_forbidden_for_doctor(doctor_client, monday_slots):
    response = doctor_client.get(
        reverse("booking-slots"), {"doctor": monday_slots.id, "date": "2026-07-27"}
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_patient_books_free_slot(patient_client, patient, monday_slots):
    response = patient_client.post(
        reverse("appointment-create"),
        {
            "doctor": monday_slots.id,
            "date": "2026-07-27",
            "time": "08:00",
            "reason": "Rotina",
        },
    )
    assert response.status_code == 201
    created = Appointment.objects.get()
    assert created.patient == patient
    assert timezone.localtime(created.appointment_date).time() == datetime.time(8, 0)


@pytest.mark.django_db
def test_booking_taken_slot_rejected(patient_client, patient, monday_slots):
    book(monday_slots, datetime.datetime(2026, 7, 27, 8, 0), patient=patient)
    response = patient_client.post(
        reverse("appointment-create"),
        {"doctor": monday_slots.id, "date": "2026-07-27", "time": "08:00"},
    )
    assert response.status_code == 422
    assert Appointment.objects.count() == 1


@pytest.mark.django_db
def test_booking_outside_availability_rejected(patient_client, monday_slots):
    response = patient_client.post(
        reverse("appointment-create"),
        {"doctor": monday_slots.id, "date": "2026-07-27", "time": "12:00"},
    )
    assert response.status_code == 422
    assert not Appointment.objects.exists()


@pytest.mark.django_db
def test_admin_books_for_chosen_patient(admin_client, patient, monday_slots):
    response = admin_client.post(
        reverse("appointment-create"),
        {
            "patient": patient.id,
            "doctor": monday_slots.id,
            "date": "2026-07-27",
            "time": "08:30",
        },
    )
    assert response.status_code == 201
    assert Appointment.objects.get().patient == patient


@pytest.mark.django_db
def test_patient_cannot_double_book_same_time(patient_client, patient, monday_slots):
    other_doctor = monday_slots.__class__.objects.create(
        first_name="Rita", last_name="Nunes", specialty="Ortopedia",
        email="rita@example.com", crm_number="CRM-9999",
    )
    WeeklySlot.objects.create(doctor=other_doctor, weekday=0, start_time=datetime.time(8, 0))
    book(other_doctor, datetime.datetime(2026, 7, 27, 8, 0), patient=patient)
    response = patient_client.post(
        reverse("appointment-create"),
        {"doctor": monday_slots.id, "date": "2026-07-27", "time": "08:00"},
    )
    assert response.status_code == 422
    assert Appointment.objects.count() == 1


@pytest.mark.django_db
def test_booking_past_date_rejected(patient_client, doctor):
    WeeklySlot.objects.create(doctor=doctor, weekday=0, start_time=datetime.time(8, 0))
    response = patient_client.post(
        reverse("appointment-create"),
        {"doctor": doctor.id, "date": "2026-07-13", "time": "08:00"},
    )
    assert response.status_code == 422
    assert not Appointment.objects.exists()


@pytest.mark.django_db
def test_booking_form_hides_other_patients_and_status(patient_client):
    Patient.objects.create(first_name="Zeca", last_name="Moura")
    html = patient_client.get(reverse("index")).content.decode()
    assert "Zeca" not in html
    assert "Status" not in html
