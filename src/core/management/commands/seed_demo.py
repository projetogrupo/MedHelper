"""Create demo accounts and availability so a fresh install is usable.

Idempotent on purpose: the Docker entrypoint runs it on every start, so it
must never fail or duplicate data when the database is already seeded.
"""
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Doctor, Patient, User, WeeklySlot

DEMO_PASSWORD = "medhelper123"

DOCTORS = [
    {
        "email": "cardio@medhelper.local",
        "first_name": "Bruno",
        "last_name": "Costa",
        "specialty": "Cardiologia",
        "crm_number": "CRM-1234",
    },
    {
        "email": "derma@medhelper.local",
        "first_name": "Rita",
        "last_name": "Nunes",
        "specialty": "Dermatologia",
        "crm_number": "CRM-5678",
    },
]

PATIENTS = [
    {"email": "ana@medhelper.local", "first_name": "Ana", "last_name": "Silva"},
    {"email": "zeca@medhelper.local", "first_name": "Zeca", "last_name": "Moura"},
]

# Monday-Friday, morning and afternoon.
SLOT_WEEKDAYS = range(5)
SLOT_HOURS = (9, 10, 11, 14, 15, 16)


class Command(BaseCommand):
    help = "Create demo users, doctors with availability, and patients."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEMO_PASSWORD,
            help=f"Password for every demo account (default: {DEMO_PASSWORD}).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]

        if User.objects.exists():
            self.stdout.write("Users already exist; skipping demo seed.")
            return

        User.objects.create_superuser("admin@medhelper.local", password)

        for spec in DOCTORS:
            user = User.objects.create_user(spec["email"], password=password)
            doctor = Doctor.objects.create(user=user, email=spec["email"], **{
                key: value for key, value in spec.items() if key != "email"
            })
            WeeklySlot.objects.bulk_create(
                WeeklySlot(doctor=doctor, weekday=weekday, start_time=datetime.time(hour, 0))
                for weekday in SLOT_WEEKDAYS
                for hour in SLOT_HOURS
            )

        for spec in PATIENTS:
            user = User.objects.create_user(spec["email"], password=password)
            Patient.objects.create(user=user, email=spec["email"], **{
                key: value for key, value in spec.items() if key != "email"
            })

        self.stdout.write(self.style.SUCCESS(
            f"Demo data created. Log in with any of these (password: {password}):\n"
            f"  admin@medhelper.local          (admin)\n"
            + "".join(f"  {d['email']:<30} ({d['specialty']})\n" for d in DOCTORS)
            + "".join(f"  {p['email']:<30} (patient)\n" for p in PATIENTS)
        ))
