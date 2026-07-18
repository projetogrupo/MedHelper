from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", views.signup, name="signup"),
    path("signup/paciente/", views.signup_patient, name="signup-patient"),
    path("signup/medico/", views.signup_doctor, name="signup-doctor"),
    path("appointments/", views.list_appointments, name="appointment-list"),
    path("appointments/create/", views.create_appointment, name="appointment-create"),
    path("appointments/<int:appointment_id>/update/", views.update_appointment, name="appointment-update"),
    path("appointments/<int:appointment_id>/delete/", views.delete_appointment, name="appointment-delete"),
    path("appointments/<int:appointment_id>/cancel/", views.cancel_appointment, name="appointment-cancel"),
]
