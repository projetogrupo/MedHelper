from django import forms

from .models import Appointment, Doctor, Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["first_name", "last_name", "birth_date", "email", "phone", "address"]


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ["first_name", "last_name", "specialty", "email", "phone", "crm_number"]


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "appointment_date", "reason", "status", "transcript"]
