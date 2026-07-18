import datetime

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import AppointmentForm, DoctorSignupForm, PatientSignupForm
from .models import Appointment, WeeklySlot


def role_of(user):
    if user.is_superuser:
        return "admin"
    if getattr(user, "doctor", None):
        return "doctor"
    if getattr(user, "patient", None):
        return "patient"
    return None


@require_http_methods(["GET"])
def signup(request):
    return render(request, "core/signup.html")


def _signup(request, form_class, template):
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("index")
    return render(request, template, {"form": form})


@require_http_methods(["GET", "POST"])
def signup_patient(request):
    return _signup(request, PatientSignupForm, "core/signup_patient.html")


@require_http_methods(["GET", "POST"])
def signup_doctor(request):
    return _signup(request, DoctorSignupForm, "core/signup_doctor.html")


WEEKDAYS = [(0, "Seg"), (1, "Ter"), (2, "Qua"), (3, "Qui"), (4, "Sex"), (5, "Sáb"), (6, "Dom")]
GRID_START = datetime.time(7, 0)
GRID_END = datetime.time(19, 0)


def grid_times(duration):
    times = []
    current = datetime.datetime.combine(datetime.date.today(), GRID_START)
    end = datetime.datetime.combine(datetime.date.today(), GRID_END)
    while current < end:
        times.append(current.time())
        current += datetime.timedelta(minutes=duration)
    return times


def weekly_grid_rows(doctor):
    painted = {
        (slot.weekday, slot.start_time)
        for slot in doctor.weekly_slots.all()
    }
    rows = []
    for time in grid_times(doctor.appointment_duration):
        cells = [
            {"weekday": weekday, "time": time, "on": (weekday, time) in painted}
            for weekday, _ in WEEKDAYS
        ]
        rows.append({"time": time, "cells": cells})
    return rows


@login_required
@require_http_methods(["GET"])
def calendar(request):
    doctor = getattr(request.user, "doctor", None)
    if doctor is None:
        return HttpResponse(status=403)
    return render(request, "core/calendar.html", {
        "doctor": doctor,
        "weekdays": WEEKDAYS,
        "rows": weekly_grid_rows(doctor),
    })


@login_required
@require_http_methods(["POST"])
def calendar_toggle(request):
    doctor = getattr(request.user, "doctor", None)
    if doctor is None:
        return HttpResponse(status=403)
    weekday = int(request.POST["weekday"])
    time = datetime.datetime.strptime(request.POST["time"], "%H:%M").time()
    slot, created = WeeklySlot.objects.get_or_create(
        doctor=doctor, weekday=weekday, start_time=time
    )
    if not created:
        slot.delete()
    return render(request, "core/weekly_cell.html", {
        "cell": {"weekday": weekday, "time": time, "on": created},
    })


@login_required
@require_http_methods(["POST"])
def calendar_duration(request):
    doctor = getattr(request.user, "doctor", None)
    if doctor is None:
        return HttpResponse(status=403)
    try:
        duration = int(request.POST.get("duration", ""))
    except ValueError:
        return redirect("calendar")
    if duration < 5 or duration > 240:
        return redirect("calendar")
    doctor.appointment_duration = duration
    doctor.save()
    base = GRID_START.hour * 60 + GRID_START.minute
    for slot in doctor.weekly_slots.all():
        minutes = slot.start_time.hour * 60 + slot.start_time.minute
        if (minutes - base) % duration != 0 or not (GRID_START <= slot.start_time < GRID_END):
            slot.delete()
    return redirect("calendar")


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
