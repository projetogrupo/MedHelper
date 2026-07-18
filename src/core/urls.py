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
    path("horarios/", views.calendar, name="calendar"),
    path("horarios/toggle/", views.calendar_toggle, name="calendar-toggle"),
    path("horarios/duracao/", views.calendar_duration, name="calendar-duration"),
    path("horarios/mes/", views.calendar_month, name="calendar-month"),
    path("horarios/dia/", views.calendar_day, name="calendar-day"),
    path("horarios/dia/personalizar/", views.calendar_day_customize, name="calendar-day-customize"),
    path("horarios/dia/toggle/", views.calendar_day_toggle, name="calendar-day-toggle"),
    path("horarios/dia/remover/", views.calendar_day_remove, name="calendar-day-remove"),
    path("appointments/", views.list_appointments, name="appointment-list"),
    path("appointments/create/", views.create_appointment, name="appointment-create"),
    path("appointments/panel/", views.booking_panel, name="booking-panel"),
    path("appointments/day/", views.booking_day, name="booking-day"),
    path("appointments/<int:appointment_id>/update/", views.update_appointment, name="appointment-update"),
    path("appointments/<int:appointment_id>/delete/", views.delete_appointment, name="appointment-delete"),
    path("appointments/<int:appointment_id>/cancel/", views.cancel_appointment, name="appointment-cancel"),
    path("appointments/<int:appointment_id>/complete/", views.complete_appointment, name="appointment-complete"),
]
