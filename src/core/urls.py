from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("patients/create/", views.create_patient, name="patient-create"),
    path("doctors/create/", views.create_doctor, name="doctor-create"),
    path("appointments/", views.list_appointments, name="appointment-list"),
    path("appointments/create/", views.create_appointment, name="appointment-create"),
    path("appointments/<int:appointment_id>/update/", views.update_appointment, name="appointment-update"),
    path("appointments/<int:appointment_id>/delete/", views.delete_appointment, name="appointment-delete"),
    path("appointments/<int:appointment_id>/cancel/", views.cancel_appointment, name="appointment-cancel"),
]
