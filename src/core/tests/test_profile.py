import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04"
    b"\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


@pytest.mark.django_db
def test_profile_requires_login():
    response = Client().get(reverse("profile"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_patient_sees_and_edits_profile(patient_client, patient):
    html = patient_client.get(reverse("profile")).content.decode()
    assert "Ana" in html
    response = patient_client.post(
        reverse("profile"),
        {"first_name": "Anna", "last_name": "Silva"},
    )
    patient.refresh_from_db()
    assert response.status_code == 302
    assert patient.first_name == "Anna"


@pytest.mark.django_db
def test_doctor_profile_edits_specialty(doctor_client, doctor):
    html = doctor_client.get(reverse("profile")).content.decode()
    assert "Especialidade" in html
    response = doctor_client.post(
        reverse("profile"),
        {
            "first_name": "Bruno",
            "last_name": "Costa",
            "specialty": "Geriatria",
            "crm_number": "CRM-0001",
            "email": "bruno@example.com",
        },
    )
    doctor.refresh_from_db()
    assert response.status_code == 302
    assert doctor.specialty == "Geriatria"


@pytest.mark.django_db
def test_photo_upload(patient_client, patient, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    response = patient_client.post(
        reverse("profile"),
        {
            "first_name": "Ana",
            "last_name": "Silva",
            "photo": SimpleUploadedFile("me.gif", GIF, "image/gif"),
        },
    )
    patient.refresh_from_db()
    assert response.status_code == 302
    assert patient.photo.name


@pytest.mark.django_db
def test_admin_has_no_profile_screen(admin_client):
    response = admin_client.get(reverse("profile"))
    assert response.status_code == 302
    assert response.url == reverse("index")


@pytest.mark.django_db
def test_nav_links_to_profile(patient_client):
    html = patient_client.get(reverse("index")).content.decode()
    assert "Perfil" in html
