from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Appointment, Doctor, Patient, User


class DoctorInline(admin.StackedInline):
    model = Doctor


class PatientInline(admin.StackedInline):
    model = Patient


@admin.register(User)
class MedHelperUserAdmin(UserAdmin):
    inlines = (DoctorInline, PatientInline)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),
    )
    list_display = ('email', 'is_staff')
    search_fields = ('email',)
    ordering = ('email',)


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