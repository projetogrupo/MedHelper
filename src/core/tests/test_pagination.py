"""Tests for paging the appointment lists and for their query cost.

The query-count test is the point of this file: the listing used to issue two
extra queries per row, so it got slower in proportion to the data.
"""
import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from core.models import Appointment
from core.views import PAGE_SIZE


def make_appointments(doctor, patient, count):
    Appointment.objects.bulk_create([
        Appointment(
            doctor=doctor, patient=patient, reason=f"consulta {index}",
            appointment_date=timezone.now() + datetime.timedelta(days=30, minutes=index * 30),
        )
        for index in range(count)
    ])


@pytest.mark.django_db
def test_first_page_is_capped(admin_client, doctor, patient):
    make_appointments(doctor, patient, PAGE_SIZE + 7)
    html = admin_client.get(reverse("appointment-list")).content.decode()
    assert html.count('<tr id="appointment-') == PAGE_SIZE


@pytest.mark.django_db
def test_second_page_holds_the_remainder(admin_client, doctor, patient):
    make_appointments(doctor, patient, PAGE_SIZE + 7)
    html = admin_client.get(reverse("appointment-list"), {"page": 2}).content.decode()
    assert html.count('<tr id="appointment-') == 7


@pytest.mark.django_db
def test_controls_are_hidden_when_everything_fits(admin_client, doctor, patient):
    make_appointments(doctor, patient, 3)
    html = admin_client.get(reverse("appointment-list")).content.decode()
    assert "Próxima" not in html


@pytest.mark.django_db
def test_controls_appear_when_there_is_more(admin_client, doctor, patient):
    make_appointments(doctor, patient, PAGE_SIZE + 1)
    html = admin_client.get(reverse("appointment-list")).content.decode()
    assert "Próxima" in html
    assert f"de {2}" in html


@pytest.mark.django_db
def test_paging_keeps_the_search_term(admin_client, doctor, patient):
    """Paging a filtered list must not silently drop the filter."""
    make_appointments(doctor, patient, PAGE_SIZE + 5)
    response = admin_client.get(
        reverse("appointment-list"), {"q": patient.first_name, "page": 2}
    )
    html = response.content.decode()
    assert response.context["appointments"].paginator.count == PAGE_SIZE + 5
    assert f"q={patient.first_name}" in html


@pytest.mark.django_db
def test_out_of_range_page_falls_back(admin_client, doctor, patient):
    make_appointments(doctor, patient, 3)
    assert admin_client.get(
        reverse("appointment-list"), {"page": 99}
    ).status_code == 200


@pytest.mark.django_db
def test_listing_cost_does_not_grow_with_the_rows(
    admin_client, doctor, patient, django_assert_max_num_queries
):
    """Guards the select_related: without it this is 2 queries per row."""
    make_appointments(doctor, patient, PAGE_SIZE)
    with django_assert_max_num_queries(10):
        admin_client.get(reverse("appointment-list"))


@pytest.mark.django_db
def test_doctor_agenda_is_paginated_too(doctor_client, doctor, patient):
    make_appointments(doctor, patient, PAGE_SIZE + 4)
    html = doctor_client.get(reverse("appointment-list")).content.decode()
    assert html.count('<tr id="appointment-') == PAGE_SIZE
    assert "Próxima" in html


@pytest.mark.django_db
def test_patient_list_is_not_paginated(patient_client, doctor, patient):
    """A patient sees their own upcoming and past lists whole."""
    make_appointments(doctor, patient, PAGE_SIZE + 4)
    html = patient_client.get(reverse("appointment-list")).content.decode()
    assert html.count('<tr id="appointment-') == PAGE_SIZE + 4
