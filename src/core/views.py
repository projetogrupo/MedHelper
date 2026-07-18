import datetime
from calendar import Calendar as MonthGrid

from django.utils import timezone

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import AppointmentForm, BookingForm, DoctorSignupForm, PatientSignupForm
from .models import Appointment, DateOverride, DateSlot, Doctor, Patient, WeeklySlot


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
    year, month = parse_month(request)
    context = {
        "doctor": doctor,
        "weekdays": WEEKDAYS,
        "rows": weekly_grid_rows(doctor),
    }
    context.update(doctor_month_context(doctor, year, month))
    return render(request, "core/calendar.html", context)


@login_required
@require_http_methods(["GET"])
def calendar_month(request):
    doctor = getattr(request.user, "doctor", None)
    if doctor is None:
        return HttpResponse(status=403)
    year, month = parse_month(request)
    return render(request, "core/calendar_month.html", doctor_month_context(doctor, year, month))


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


def day_panel_context(doctor, date):
    override = doctor.date_overrides.filter(date=date).first()
    if override is not None:
        painted = set(override.slots.values_list("start_time", flat=True))
    else:
        painted = set(
            doctor.weekly_slots.filter(weekday=date.weekday()).values_list("start_time", flat=True)
        )
    cells = [
        {"time": time, "on": time in painted}
        for time in grid_times(doctor.appointment_duration)
    ]
    return {"date": date, "override": override, "cells": cells}


def parse_day(value):
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


@login_required
@require_http_methods(["GET"])
def calendar_day(request):
    doctor = getattr(request.user, "doctor", None)
    if doctor is None:
        return HttpResponse(status=403)
    date = parse_day(request.GET.get("date"))
    if date is None:
        return HttpResponse(status=400)
    return render(request, "core/day_panel.html", day_panel_context(doctor, date))


@login_required
@require_http_methods(["POST"])
def calendar_day_customize(request):
    doctor = getattr(request.user, "doctor", None)
    if doctor is None:
        return HttpResponse(status=403)
    date = parse_day(request.POST.get("date"))
    if date is None:
        return HttpResponse(status=400)
    override, created = DateOverride.objects.get_or_create(doctor=doctor, date=date)
    if created:
        for slot in doctor.weekly_slots.filter(weekday=date.weekday()):
            DateSlot.objects.create(override=override, start_time=slot.start_time)
    return render(request, "core/day_panel.html", day_panel_context(doctor, date))


@login_required
@require_http_methods(["POST"])
def calendar_day_toggle(request):
    doctor = getattr(request.user, "doctor", None)
    if doctor is None:
        return HttpResponse(status=403)
    date = parse_day(request.POST.get("date"))
    if date is None:
        return HttpResponse(status=400)
    override = get_object_or_404(DateOverride, doctor=doctor, date=date)
    time = datetime.datetime.strptime(request.POST["time"], "%H:%M").time()
    slot, created = DateSlot.objects.get_or_create(override=override, start_time=time)
    if not created:
        slot.delete()
    return render(request, "core/day_cell.html", {
        "date": date,
        "cell": {"time": time, "on": created},
    })


@login_required
@require_http_methods(["POST"])
def calendar_day_remove(request):
    doctor = getattr(request.user, "doctor", None)
    if doctor is None:
        return HttpResponse(status=403)
    date = parse_day(request.POST.get("date"))
    if date is None:
        return HttpResponse(status=400)
    DateOverride.objects.filter(doctor=doctor, date=date).delete()
    return render(request, "core/day_panel.html", day_panel_context(doctor, date))


MONTHS_PT = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def booking_filters(request):
    specialty = request.GET.get("specialty", "").strip()
    doctor_id = request.GET.get("doctor", "").strip()
    if doctor_id and specialty and not Doctor.objects.filter(id=doctor_id, specialty=specialty).exists():
        doctor_id = ""
    if doctor_id:
        doctors = Doctor.objects.filter(id=doctor_id)
    elif specialty:
        doctors = Doctor.objects.filter(specialty=specialty)
    else:
        doctors = Doctor.objects.none()
    return specialty, doctor_id, doctors


def parse_month(request):
    today = datetime.date.today()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        datetime.date(year, month, 1)
    except ValueError:
        year, month = today.year, today.month
    return year, month


def month_nav(year, month):
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    return {
        "month_label": f"{MONTHS_PT[month]} {year}",
        "year": year, "month": month,
        "prev_year": prev_year, "prev_month": prev_month,
        "next_year": next_year, "next_month": next_month,
    }


def booking_panel_context(request):
    today = datetime.date.today()
    year, month = parse_month(request)
    specialty, doctor_id, doctors = booking_filters(request)
    doctors = list(doctors)
    weeks = []
    for week in MonthGrid().monthdatescalendar(year, month):
        row = []
        for day in week:
            available = (
                day.month == month
                and day >= today
                and any(d.available_slots(day) for d in doctors)
            )
            row.append({"date": day, "in_month": day.month == month, "available": available})
        weeks.append(row)
    context = {
        "specialties": Doctor.objects.order_by("specialty").values_list("specialty", flat=True).distinct(),
        "all_doctors": Doctor.objects.filter(specialty=specialty) if specialty else Doctor.objects.all(),
        "selected_specialty": specialty,
        "selected_doctor": doctor_id,
        "has_filter": bool(specialty or doctor_id),
        "weeks": weeks,
    }
    context.update(month_nav(year, month))
    return context


def doctor_month_context(doctor, year, month):
    today = datetime.date.today()
    customized = set(
        doctor.date_overrides.filter(
            date__year=year, date__month=month
        ).values_list("date", flat=True)
    )
    weeks = []
    for week in MonthGrid().monthdatescalendar(year, month):
        row = []
        for day in week:
            row.append({
                "date": day,
                "in_month": day.month == month,
                "future": day >= today,
                "available": day >= today and bool(doctor.slots_for_date(day)),
                "customized": day in customized,
            })
        weeks.append(row)
    context = {"weeks": weeks}
    context.update(month_nav(year, month))
    return context


@login_required
def index(request):
    if role_of(request.user) == "doctor":
        return redirect("appointment-list")
    context = booking_panel_context(request)
    context["patients"] = Patient.objects.all() if request.user.is_superuser else None
    return render(request, "core/index.html", context)


@login_required
@require_http_methods(["GET"])
def booking_panel(request):
    if role_of(request.user) not in ("patient", "admin"):
        return HttpResponse(status=403)
    return render(request, "core/booking_area.html", booking_panel_context(request))


@login_required
@require_http_methods(["GET"])
def booking_day(request):
    if role_of(request.user) not in ("patient", "admin"):
        return HttpResponse(status=403)
    date = parse_day(request.GET.get("date"))
    if date is None:
        return HttpResponse(status=400)
    _, doctor_id, doctors = booking_filters(request)
    groups = []
    for doctor in doctors:
        times = doctor.available_slots(date)
        if times:
            groups.append({"doctor": doctor, "times": times})
    return render(request, "core/day_options.html", {
        "date": date,
        "groups": groups,
        "show_doctor_names": not doctor_id,
    })


@login_required
@require_http_methods(["GET"])
def list_appointments(request):
    query = request.GET.get("q", "").strip()
    role = role_of(request.user)
    if role == "patient":
        own = Appointment.objects.filter(patient=request.user.patient)
        now = timezone.now()
        return render(request, "core/patient_appointments.html", {
            "upcoming": own.filter(appointment_date__gte=now).order_by("appointment_date"),
            "past": own.filter(appointment_date__lt=now).order_by("-appointment_date"),
        })
    if role == "doctor":
        appointments = Appointment.objects.filter(doctor=request.user.doctor)
        if query:
            appointments = appointments.filter(
                Q(patient__first_name__icontains=query)
                | Q(patient__last_name__icontains=query)
            )
        return render(request, "core/doctor_agenda.html", {
            "appointments": appointments.order_by("appointment_date"),
        })
    appointments = Appointment.objects.all()
    if query:
        appointments = appointments.filter(
            Q(patient__first_name__icontains=query)
            | Q(patient__last_name__icontains=query)
        )
    return render(request, "core/appointment_list.html", {"appointments": appointments})


@login_required
@require_http_methods(["POST"])
def create_appointment(request):
    role = role_of(request.user)
    if role == "doctor":
        return HttpResponse(status=403)
    data = request.POST.copy()
    slot = data.get("slot", "")
    if "|" in slot:
        doctor_id, _, slot_time = slot.partition("|")
        data["doctor"] = doctor_id
        data["time"] = slot_time
    form = BookingForm(data)
    if form.is_valid():
        patient = form.cleaned_data.get("patient")
        if role == "patient":
            patient = request.user.patient
        when = timezone.make_aware(
            datetime.datetime.combine(
                form.cleaned_data["date"], form.cleaned_data["time"]
            )
        )
        if patient is None:
            form.add_error("patient", "Escolha um paciente.")
        elif Appointment.objects.filter(
            patient=patient, appointment_date=when
        ).exclude(status=Appointment.STATUS_CANCELLED).exists():
            form.add_error(None, "O paciente já tem uma consulta nesse horário.")
        else:
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=form.cleaned_data["doctor"],
                appointment_date=when,
            )
            return render(request, "core/booking_confirm.html", {"appointment": appointment}, status=201)
    return render(request, "core/booking_errors.html", {"form": form}, status=422)


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


def cancel_item_template(role):
    if role == "patient":
        return "core/patient_appointment_item.html"
    if role == "doctor":
        return "core/doctor_appointment_item.html"
    return "core/appointment_item.html"


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
        return render(request, cancel_item_template(role), {"appointment": appointment}, status=422)
    appointment.status = Appointment.STATUS_CANCELLED
    appointment.save()
    return render(request, cancel_item_template(role), {"appointment": appointment}, status=200)
