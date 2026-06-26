from django.db import models


class Patient(models.Model):
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
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	specialty = models.CharField(max_length=120)
	# make email unique for doctors (optional) and allow NULL so multiple empty values
	email = models.EmailField(max_length=254, blank=True, null=True, unique=True)
	phone = models.CharField(max_length=20, blank=True)
	# CRM is an identifier for a doctor; make it unique when present
	crm_number = models.CharField(max_length=50, blank=True, null=True, unique=True)

	class Meta:
		ordering = ['last_name', 'first_name']

	def __str__(self):
		return f"Dr. {self.first_name} {self.last_name}"


class Appointment(models.Model):
	STATUS_SCHEDULED = 'scheduled'
	STATUS_COMPLETED = 'completed'
	STATUS_CANCELLED = 'cancelled'

	STATUS_CHOICES = [
		(STATUS_SCHEDULED, 'Scheduled'),
		(STATUS_COMPLETED, 'Completed'),
		(STATUS_CANCELLED, 'Cancelled'),
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