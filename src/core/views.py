from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import AppointmentForm
from .models import Appointment


def role_of(user):
    if user.is_superuser:
        return "admin"
    if getattr(user, "doctor", None):
        return "doctor"
    if getattr(user, "patient", None):
        return "patient"
    return None


@login_required
def index(request):
    if role_of(request.user) == "doctor":
        return redirect("appointment-list")
    return render(request, "core/index.html", {
        "appointment_form": AppointmentForm(),
    })


@login_required
@require_http_methods(["GET"])
def list_appointments(request):
    query = request.GET.get("q", "").strip()
    appointments = Appointment.objects.all()
    role = role_of(request.user)
    if role == "doctor":
        appointments = appointments.filter(doctor=request.user.doctor)
    elif role == "patient":
        appointments = appointments.filter(patient=request.user.patient)
    if query:
        appointments = appointments.filter(
            Q(patient__first_name__icontains=query)
            | Q(patient__last_name__icontains=query)
        )
    return render(request, "core/appointment_list.html", {"appointments": appointments})


@login_required
@require_http_methods(["POST"])
def create_appointment(request):
    data = request.POST
    if role_of(request.user) == "patient":
        data = request.POST.copy()
        data["patient"] = request.user.patient.id
    form = AppointmentForm(data)
    if form.is_valid():
        appointment = form.save()
        return render(request, "core/appointment_item.html", {"appointment": appointment}, status=201)
    return render(request, "core/appointment_form.html", {"form": form}, status=422)


@login_required
@require_http_methods(["PUT"])
def update_appointment(request, appointment_id):
    if not request.user.is_superuser:
        return HttpResponse(status=403)
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


@login_required
@require_http_methods(["DELETE"])
def delete_appointment(request, appointment_id):
    if not request.user.is_superuser:
        return HttpResponse(status=403)
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()
    return HttpResponse(status=200)


@login_required
@require_http_methods(["POST"])
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    role = role_of(request.user)
    if role == "doctor" and appointment.doctor != request.user.doctor:
        return HttpResponse(status=403)
    if role == "patient" and appointment.patient != request.user.patient:
        return HttpResponse(status=403)
    if not appointment.is_cancellable:
        return render(request, "core/appointment_item.html", {"appointment": appointment}, status=422)
    appointment.status = Appointment.STATUS_CANCELLED
    appointment.save()
    return render(request, "core/appointment_item.html", {"appointment": appointment}, status=200)
