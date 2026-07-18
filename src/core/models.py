import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone


class Patient(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	birth_date = models.DateField(null=True, blank=True)
	email = models.EmailField(max_length=254, blank=True)
	phone = models.CharField(max_length=20, blank=True)
	address = models.CharField(max_length=255, blank=True)

	class Meta:
		ordering = ['last_name', 'first_name']

	def __str__(self):
		return f"{self.first_name} {self.last_name}"


class Doctor(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	specialty = models.CharField(max_length=120)
	# make email unique for doctors (optional) and allow NULL so multiple empty values
	email = models.EmailField(max_length=254, blank=True, null=True, unique=True)
	phone = models.CharField(max_length=20, blank=True)
	# CRM is an identifier for a doctor; make it unique when present
	crm_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
	appointment_duration = models.PositiveIntegerField(default=30)

	class Meta:
		ordering = ['last_name', 'first_name']

	def __str__(self):
		return f"Dr. {self.first_name} {self.last_name}"

	def slots_for_date(self, date):
		override = self.date_overrides.filter(date=date).first()
		if override is not None:
			return sorted(override.slots.values_list('start_time', flat=True))
		return sorted(
			self.weekly_slots.filter(weekday=date.weekday()).values_list('start_time', flat=True)
		)

	def available_slots(self, date):
		taken = {
			timezone.localtime(appointment.appointment_date).time()
			for appointment in self.appointments.filter(
				appointment_date__date=date
			).exclude(status=Appointment.STATUS_CANCELLED)
		}
		now = timezone.localtime()
		result = []
		for time in self.slots_for_date(date):
			if time in taken:
				continue
			when = timezone.make_aware(datetime.datetime.combine(date, time))
			if when <= now:
				continue
			result.append(time)
		return result


class WeeklySlot(models.Model):
	doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='weekly_slots')
	weekday = models.PositiveSmallIntegerField()
	start_time = models.TimeField()

	class Meta:
		ordering = ['weekday', 'start_time']
		constraints = [
			models.UniqueConstraint(fields=['doctor', 'weekday', 'start_time'], name='unique_weekly_slot'),
		]

	def __str__(self):
		return f"{self.doctor} {self.weekday} {self.start_time}"


class DateOverride(models.Model):
	doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='date_overrides')
	date = models.DateField()

	class Meta:
		ordering = ['date']
		constraints = [
			models.UniqueConstraint(fields=['doctor', 'date'], name='unique_date_override'),
		]

	def __str__(self):
		return f"{self.doctor} {self.date}"


class DateSlot(models.Model):
	override = models.ForeignKey(DateOverride, on_delete=models.CASCADE, related_name='slots')
	start_time = models.TimeField()

	class Meta:
		ordering = ['start_time']
		constraints = [
			models.UniqueConstraint(fields=['override', 'start_time'], name='unique_date_slot'),
		]

	def __str__(self):
		return f"{self.override} {self.start_time}"


class Appointment(models.Model):
	STATUS_SCHEDULED = 'scheduled'
	STATUS_COMPLETED = 'completed'
	STATUS_CANCELLED = 'cancelled'

	STATUS_CHOICES = [
		(STATUS_SCHEDULED, 'Agendada'),
		(STATUS_COMPLETED, 'Concluída'),
		(STATUS_CANCELLED, 'Cancelada'),
	]

	# Keep appointment records even if a patient/doctor is deleted.
	# Use SET_NULL so the appointment remains while the FK becomes NULL.
	patient = models.ForeignKey(
		Patient,
		on_delete=models.SET_NULL,
		related_name='appointments',
		null=True,
		blank=True,
	)
	doctor = models.ForeignKey(
		Doctor,
		on_delete=models.SET_NULL,
		related_name='appointments',
		null=True,
		blank=True,
	)

	appointment_date = models.DateTimeField()
	reason = models.TextField(blank=True)

	status = models.CharField(
		max_length=20,
		choices=STATUS_CHOICES,
		default=STATUS_SCHEDULED
	)

	transcript = models.TextField(blank=True)

	transcript_pdf = models.FileField(
		upload_to='appointment_transcripts/',
		blank=True,
		null=True
	)

	transcript_created_at = models.DateTimeField(
		null=True,
		blank=True
	)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-appointment_date']

	def __str__(self):
		return (
			f"{self.patient} with "
			f"{self.doctor} on "
			f"{self.appointment_date:%Y-%m-%d %H:%M}"
		)

	@property
	def is_cancellable(self):
		return self.status == self.STATUS_SCHEDULED

	@property
	def is_overdue(self):
		return self.status == self.STATUS_SCHEDULED and self.appointment_date < timezone.now()