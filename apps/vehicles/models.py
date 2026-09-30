from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator


class Vehicle(models.Model):
    """A customer-owned vehicle. 1:N with owner, 1:N with MaintenanceRecord/Appointment."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vehicles"
    )
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    vin = models.CharField("VIN", max_length=17, unique=True)
    license_plate = models.CharField(max_length=20, unique=True)
    current_mileage_km = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(check=models.Q(year__gte=1950), name="vehicle_year_realistic"),
        ]

    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.license_plate})"


class ServiceType(models.Model):
    """Catalog of maintenance service offerings with recommended intervals,
    used by the AI agent to compute overdue services."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    recommended_interval_km = models.PositiveIntegerField(
        help_text="Recommended mileage interval between services, in km."
    )
    recommended_interval_months = models.PositiveIntegerField(
        help_text="Recommended time interval between services, in months."
    )
    base_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.name


class TechnicianProfile(models.Model):
    """Extra attributes for users with role=TECHNICIAN (1:1 extension table)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="technician_profile"
    )
    specialty = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Technician: {self.user.username}"


class SparePart(models.Model):
    """Inventory item; M:N with Appointment through AppointmentPart."""

    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    stock_quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(stock_quantity__gte=0), name="stock_non_negative"),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Appointment(models.Model):
    """A booked maintenance appointment. Central entity the Agentic AI acts on."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Confirmation"
        CONFIRMED = "CONFIRMED", "Confirmed"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="appointments")
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT, related_name="appointments")
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_appointments",
        limit_choices_to={"role": "TECHNICIAN"},
    )
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_by_agent = models.BooleanField(
        default=False, help_text="True if this appointment was created via the AI agent tool-call."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    spare_parts = models.ManyToManyField(SparePart, through="AppointmentPart", related_name="appointments")

    class Meta:
        ordering = ["scheduled_at"]
        indexes = [models.Index(fields=["scheduled_at", "status"])]

    def __str__(self):
        return f"{self.vehicle} - {self.service_type} @ {self.scheduled_at:%Y-%m-%d %H:%M}"


class AppointmentPart(models.Model):
    """Through table for the Appointment <-> SparePart M:N relationship."""

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    spare_part = models.ForeignKey(SparePart, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("appointment", "spare_part")


class MaintenanceRecord(models.Model):
    """Historical record of completed maintenance — the data the AI agent
    reads to determine whether a service is overdue."""

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="maintenance_records")
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
    appointment = models.OneToOneField(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_record"
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        limit_choices_to={"role": "TECHNICIAN"},
    )
    performed_at = models.DateTimeField()
    mileage_at_service = models.PositiveIntegerField()
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-performed_at"]

    def __str__(self):
        return f"{self.vehicle} - {self.service_type} on {self.performed_at:%Y-%m-%d}"
