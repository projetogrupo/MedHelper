from django.contrib import admin

from .models import Appointment, Doctor, Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'email',
        'phone',
    )

    search_fields = (
        'first_name',
        'last_name',
        'email',
        'phone',
    )


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'specialty',
        'email',
        'phone',
    )

    search_fields = (
        'first_name',
        'last_name',
        'specialty',
        'email',
        'phone',
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'patient',
        'doctor',
        'appointment_date',
        'status',
        'transcript_created_at',
    )

    list_filter = (
        'status',
        'appointment_date',
        'doctor',
    )

    search_fields = (
        'patient__first_name',
        'patient__last_name',
        'doctor__first_name',
        'doctor__last_name',
        'reason',
        'transcript',
    )

    date_hierarchy = 'appointment_date'