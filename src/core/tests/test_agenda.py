import datetime

import pytest
from django.urls import reverse

from core.models import DateOverride, DateSlot, Doctor, WeeklySlot


@pytest.mark.django_db
def test_appointment_duration_defaults_to_30(doctor):
    assert doctor.appointment_duration == 30


@pytest.mark.django_db
def test_calendar_requires_doctor(patient_client, admin_client):
    assert patient_client.get(reverse("calendar")).status_code == 403
    assert admin_client.get(reverse("calendar")).status_code == 403


@pytest.mark.django_db
def test_calendar_renders_grid(doctor_client):
    response = doctor_client.get(reverse("calendar"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Seg" in html
    assert "07:00" in html


@pytest.mark.django_db
def test_toggle_creates_weekly_slot(doctor_client, doctor):
    response = doctor_client.post(
        reverse("calendar-toggle"), {"weekday": 0, "time": "08:00"}
    )
    assert response.status_code == 200
    assert WeeklySlot.objects.filter(
        doctor=doctor, weekday=0, start_time=datetime.time(8, 0)
    ).exists()


@pytest.mark.django_db
def test_toggle_twice_removes_weekly_slot(doctor_client, doctor):
    doctor_client.post(reverse("calendar-toggle"), {"weekday": 0, "time": "08:00"})
    doctor_client.post(reverse("calendar-toggle"), {"weekday": 0, "time": "08:00"})
    assert not WeeklySlot.objects.exists()


@pytest.mark.django_db
def test_update_duration(doctor_client, doctor):
    response = doctor_client.post(reverse("calendar-duration"), {"duration": 60})
    doctor.refresh_from_db()
    assert response.status_code == 302
    assert doctor.appointment_duration == 60


@pytest.mark.django_db
def test_duration_change_drops_misaligned_slots(doctor_client, doctor):
    WeeklySlot.objects.create(doctor=doctor, weekday=0, start_time=datetime.time(8, 0))
    WeeklySlot.objects.create(doctor=doctor, weekday=0, start_time=datetime.time(8, 30))
    doctor_client.post(reverse("calendar-duration"), {"duration": 60})
    remaining = list(WeeklySlot.objects.values_list("start_time", flat=True))
    assert remaining == [datetime.time(8, 0)]


@pytest.mark.django_db
def test_doctor_nav_has_calendar_link(doctor_client):
    html = doctor_client.get(reverse("appointment-list")).content.decode()
    assert "Horários" in html


@pytest.mark.django_db
def test_customize_date_copies_weekly_template(doctor_client, doctor):
    WeeklySlot.objects.create(doctor=doctor, weekday=0, start_time=datetime.time(8, 0))
    WeeklySlot.objects.create(doctor=doctor, weekday=0, start_time=datetime.time(9, 0))
    response = doctor_client.post(
        reverse("calendar-day-customize"), {"date": "2026-07-20"}
    )
    assert response.status_code == 200
    override = DateOverride.objects.get(doctor=doctor, date=datetime.date(2026, 7, 20))
    times = list(override.slots.values_list("start_time", flat=True))
    assert times == [datetime.time(8, 0), datetime.time(9, 0)]


@pytest.mark.django_db
def test_day_toggle_adds_and_removes_slot(doctor_client, doctor):
    doctor_client.post(reverse("calendar-day-customize"), {"date": "2026-07-20"})
    doctor_client.post(
        reverse("calendar-day-toggle"), {"date": "2026-07-20", "time": "10:00"}
    )
    override = DateOverride.objects.get(doctor=doctor)
    assert override.slots.filter(start_time=datetime.time(10, 0)).exists()
    doctor_client.post(
        reverse("calendar-day-toggle"), {"date": "2026-07-20", "time": "10:00"}
    )
    assert not override.slots.filter(start_time=datetime.time(10, 0)).exists()


@pytest.mark.django_db
def test_remove_customization_restores_template(doctor_client, doctor):
    doctor_client.post(reverse("calendar-day-customize"), {"date": "2026-07-20"})
    response = doctor_client.post(
        reverse("calendar-day-remove"), {"date": "2026-07-20"}
    )
    assert response.status_code == 200
    assert not DateOverride.objects.exists()


@pytest.mark.django_db
def test_slots_for_date_prefers_override(doctor):
    WeeklySlot.objects.create(doctor=doctor, weekday=0, start_time=datetime.time(8, 0))
    override = DateOverride.objects.create(doctor=doctor, date=datetime.date(2026, 7, 20))
    DateSlot.objects.create(override=override, start_time=datetime.time(14, 0))
    assert doctor.slots_for_date(datetime.date(2026, 7, 20)) == [datetime.time(14, 0)]
    assert doctor.slots_for_date(datetime.date(2026, 7, 27)) == [datetime.time(8, 0)]


@pytest.mark.django_db
def test_day_panel_requires_doctor(patient_client):
    response = patient_client.get(
        reverse("calendar-day"), {"date": "2026-07-20"}
    )
    assert response.status_code == 403
