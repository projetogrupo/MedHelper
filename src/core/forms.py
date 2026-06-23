from django import forms

from .models import Appointment, Doctor, Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'first_name',
            'last_name',
            'birth_date',
            'email',
            'phone',
            'address',
        ]
        widgets = {
            # input type="date" no navegador
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'first_name': 'Nome',
            'last_name':  'Sobrenome',
            'birth_date': 'Data de nascimento',
            'email':      'E-mail',
            'phone':      'Telefone',
            'address':    'Endereço',
        }


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = [
            'first_name',
            'last_name',
            'specialty',
            'email',
            'phone',
            'crm_number',
        ]
        labels = {
            'first_name': 'Nome',
            'last_name':  'Sobrenome',
            'specialty':  'Especialidade',
            'email':      'E-mail',
            'phone':      'Telefone',
            'crm_number': 'CRM',
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'patient',
            'doctor',
            'appointment_date',
            'reason',
            'status',
        ]
        widgets = {
            # input type="datetime-local" no navegador
            'appointment_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'patient':          'Paciente',
            'doctor':           'Médico',
            'appointment_date': 'Data e hora',
            'reason':           'Motivo',
            'status':           'Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exibe os campos de FK com os __str__ dos modelos (já definidos)
        self.fields['patient'].queryset = Patient.objects.all()
        self.fields['doctor'].queryset  = Doctor.objects.all()
        # Garante que o formato datetime-local seja lido corretamente no edit
        self.fields['appointment_date'].input_formats = ['%Y-%m-%dT%H:%M']