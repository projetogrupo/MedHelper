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
        widgets = {
            "appointment_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Accept both HTML5 datetime-local and legacy payload formats.
        self.fields["appointment_date"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
        ]
