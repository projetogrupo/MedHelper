from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Appointment, Doctor, MedicalSpecialty, Patient, User


class EmailSignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["email"]

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def save_user(self):
        return super().save()


class PatientSignupForm(EmailSignupForm):
    first_name = forms.CharField(max_length=100, label="Nome")
    last_name = forms.CharField(max_length=100, label="Sobrenome")
    birth_date = forms.DateField(
        required=False,
        label="Data de nascimento",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    phone = forms.CharField(max_length=20, required=False, label="Telefone")

    field_order = ["email", "password1", "password2", "first_name", "last_name", "birth_date", "phone"]

    def save(self, commit=True):
        user = self.save_user()
        Patient.objects.create(
            user=user,
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            birth_date=self.cleaned_data.get("birth_date"),
            email=self.cleaned_data["email"],
            phone=self.cleaned_data.get("phone") or "",
        )
        return user


class DoctorSignupForm(EmailSignupForm):
    first_name = forms.CharField(max_length=100, label="Nome")
    last_name = forms.CharField(max_length=100, label="Sobrenome")
    specialty = forms.ChoiceField(
        choices=[("", "Selecione…")] + MedicalSpecialty.choices,
        label="Especialidade",
    )
    crm_number = forms.CharField(max_length=50, required=False, label="CRM")
    phone = forms.CharField(max_length=20, required=False, label="Telefone")

    field_order = ["email", "password1", "password2", "first_name", "last_name", "specialty", "crm_number", "phone"]

    def save(self, commit=True):
        user = self.save_user()
        Doctor.objects.create(
            user=user,
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            specialty=self.cleaned_data["specialty"],
            crm_number=self.cleaned_data.get("crm_number") or None,
            email=self.cleaned_data["email"],
            phone=self.cleaned_data.get("phone") or "",
        )
        return user


class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["first_name", "last_name", "birth_date", "email", "phone", "address", "photo"]
        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "birth_date": "Data de nascimento",
            "email": "E-mail",
            "phone": "Telefone",
            "address": "Endereço",
            "photo": "Foto",
        }
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ["first_name", "last_name", "specialty", "crm_number", "email", "phone", "photo"]
        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "specialty": "Especialidade",
            "crm_number": "CRM",
            "email": "E-mail",
            "phone": "Telefone",
            "photo": "Foto",
        }


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
