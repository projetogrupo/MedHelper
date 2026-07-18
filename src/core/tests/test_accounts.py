import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
def test_doctor_links_to_user(doctor):
    user = User.objects.create_user("carla", password="x")
    doctor.user = user
    doctor.save()
    assert user.doctor == doctor


@pytest.mark.django_db
def test_patient_links_to_user(patient):
    user = User.objects.create_user("ana", password="x")
    patient.user = user
    patient.save()
    assert user.patient == patient


@pytest.mark.django_db
def test_deleting_user_keeps_doctor(doctor):
    user = User.objects.create_user("carla", password="x")
    doctor.user = user
    doctor.save()
    user.delete()
    doctor.refresh_from_db()
    assert doctor.user is None


@pytest.mark.django_db
def test_user_admin_change_page_has_profile_inlines(client):
    admin_user = User.objects.create_superuser("root", "root@example.com", "x")
    target = User.objects.create_user("carla", password="x")
    client.force_login(admin_user)
    response = client.get(reverse("admin:auth_user_change", args=[target.id]))
    html = response.content.decode()
    assert "specialty" in html
    assert "birth_date" in html
