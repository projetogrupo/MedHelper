from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Appointment, Doctor, Patient


class PatientSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label="Nome")
    last_name = forms.CharField(max_length=100, label="Sobrenome")
    birth_date = forms.DateField(
        required=False,
        label="Data de nascimento",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    email = forms.EmailField(required=False, label="E-mail")
    phone = forms.CharField(max_length=20, required=False, label="Telefone")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username"]

    def save(self, commit=True):
        user = super().save(commit)
        Patient.objects.create(
            user=user,
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            birth_date=self.cleaned_data.get("birth_date"),
            email=self.cleaned_data.get("email") or "",
            phone=self.cleaned_data.get("phone") or "",
        )
        return user


class DoctorSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label="Nome")
    last_name = forms.CharField(max_length=100, label="Sobrenome")
    specialty = forms.CharField(max_length=120, label="Especialidade")
    crm_number = forms.CharField(max_length=50, required=False, label="CRM")
    email = forms.EmailField(required=False, label="E-mail")
    phone = forms.CharField(max_length=20, required=False, label="Telefone")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username"]

    def save(self, commit=True):
        user = super().save(commit)
        Doctor.objects.create(
            user=user,
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            specialty=self.cleaned_data["specialty"],
            crm_number=self.cleaned_data.get("crm_number") or None,
            email=self.cleaned_data.get("email") or None,
            phone=self.cleaned_data.get("phone") or "",
        )
        return user


class BookingForm(forms.Form):
    patient = forms.ModelChoiceField(queryset=Patient.objects.all(), required=False, label="Paciente")
    doctor = forms.ModelChoiceField(queryset=Doctor.objects.all(), label="Médico")
    date = forms.DateField(label="Data", widget=forms.DateInput(attrs={"type": "date"}))
    time = forms.TimeField(label="Horário")

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get("doctor")
        date = cleaned.get("date")
        time = cleaned.get("time")
        if doctor and date and time and time not in doctor.available_slots(date):
            raise forms.ValidationError("Este horário não está mais disponível.")
        return cleaned


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
