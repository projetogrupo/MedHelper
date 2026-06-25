from django.db.models import Q
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .forms import AppointmentForm, DoctorForm, PatientForm
from .models import Appointment


def index(request):
    return HttpResponse("MedHelper is running.")


@require_http_methods(["POST"])
def create_patient(request):
    form = PatientForm(request.POST)
    if form.is_valid():
        patient = form.save()
        return render(request, "core/patient_item.html", {"patient": patient}, status=201)
    return render(request, "core/patient_form.html", {"form": form}, status=422)


@require_http_methods(["POST"])
def create_doctor(request):
    form = DoctorForm(request.POST)
    if form.is_valid():
        doctor = form.save()
        return render(request, "core/doctor_item.html", {"doctor": doctor}, status=201)
    return render(request, "core/doctor_form.html", {"form": form}, status=422)


@require_http_methods(["GET"])
def list_appointments(request):
    query = request.GET.get("q", "").strip()
    appointments = Appointment.objects.all()
    if query:
        appointments = appointments.filter(
            Q(patient__first_name__icontains=query)
            | Q(patient__last_name__icontains=query)
        )
    return render(request, "core/appointment_list.html", {"appointments": appointments})


@require_http_methods(["POST"])
def create_appointment(request):
    form = AppointmentForm(request.POST)
    if form.is_valid():
        appointment = form.save()
        return render(request, "core/appointment_item.html", {"appointment": appointment}, status=201)
    return render(request, "core/appointment_form.html", {"form": form}, status=422)


@require_http_methods(["PUT"])
def update_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    form = AppointmentForm(QueryDict(request.body), instance=appointment)
    if form.is_valid():
        form.save()
        return render(request, "core/appointment_item.html", {"appointment": appointment}, status=200)
    appointment.refresh_from_db()
    context = {
        "form": AppointmentForm(instance=appointment),
        "appointment": appointment,
        "error": "Invalid input - changes not saved",
    }
    return render(request, "core/appointment_update_form.html", context, status=422)


@require_http_methods(["DELETE"])
def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()
    return HttpResponse(status=200)


@require_http_methods(["POST"])
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if not appointment.is_cancellable:
        return render(request, "core/appointment_item.html", {"appointment": appointment}, status=422)
    appointment.status = Appointment.STATUS_CANCELLED
    appointment.save()
    return render(request, "core/appointment_item.html", {"appointment": appointment}, status=200)
