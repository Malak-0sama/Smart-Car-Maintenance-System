"""
Agentic AI Tool Registry.

Each tool below is a plain Python/Django function that:
  1. Receives the authenticated `user` object (Identity Binding — SRS 6.1)
  2. Explicitly checks ownership/role permissions (SRS 6.2)
  3. Validates its own parameters (SRS 6.3)
  4. Never touches the database with raw SQL — Django ORM only

The `TOOL_SCHEMAS` list is the JSON-schema description handed to the LLM
for function calling. Keep descriptions precise to avoid hallucinated
arguments (SRS section 7).
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError

from apps.vehicles.models import Vehicle, ServiceType, Appointment, MaintenanceRecord
from apps.authentication.permissions import user_owns_vehicle

BUSINESS_HOURS = range(9, 17)  # 9:00 - 17:00
SLOT_MINUTES = 60


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def get_overdue_services(user, vehicle_id: int) -> dict:
    """Identify services that are overdue for a given vehicle, based on the
    vehicle's mileage and the recency of its MaintenanceRecord history."""
    try:
        vehicle = Vehicle.objects.get(pk=vehicle_id)
    except Vehicle.DoesNotExist:
        return {"error": f"Vehicle {vehicle_id} not found."}

    if not user_owns_vehicle(user, vehicle):
        raise PermissionDenied("You do not have access to this vehicle.")

    overdue = []
    now = timezone.now()
    for service in ServiceType.objects.all():
        last_record = (
            MaintenanceRecord.objects.filter(vehicle=vehicle, service_type=service)
            .order_by("-performed_at")
            .first()
        )
        if last_record is None:
            overdue.append({
                "service_type_id": service.id,
                "service_name": service.name,
                "reason": "No record of this service ever being performed.",
            })
            continue

        km_since = vehicle.current_mileage_km - last_record.mileage_at_service
        months_since = (now - last_record.performed_at).days / 30

        if km_since >= service.recommended_interval_km or months_since >= service.recommended_interval_months:
            overdue.append({
                "service_type_id": service.id,
                "service_name": service.name,
                "reason": f"{km_since} km / {round(months_since,1)} months since last service "
                          f"(interval: {service.recommended_interval_km} km / "
                          f"{service.recommended_interval_months} months).",
            })

    return {"vehicle_id": vehicle.id, "vehicle": str(vehicle), "overdue_services": overdue}


def check_available_slots(user, service_type_id: int, days_ahead: int = 7) -> dict:
    """Return open appointment slots in the next `days_ahead` days."""
    try:
        service = ServiceType.objects.get(pk=service_type_id)
    except ServiceType.DoesNotExist:
        return {"error": f"Service type {service_type_id} not found."}

    if days_ahead < 1 or days_ahead > 30:
        raise ValidationError("days_ahead must be between 1 and 30.")

    now = timezone.now()
    taken = set(
        Appointment.objects.filter(
            scheduled_at__gte=now, scheduled_at__lte=now + timedelta(days=days_ahead),
        ).exclude(status=Appointment.Status.CANCELLED).values_list("scheduled_at", flat=True)
    )

    available = []
    for day_offset in range(days_ahead):
        day = (now + timedelta(days=day_offset + 1)).replace(minute=0, second=0, microsecond=0)
        for hour in BUSINESS_HOURS:
            slot = day.replace(hour=hour)
            if slot not in taken:
                available.append(slot.isoformat())
        if len(available) >= 10:
            break

    return {"service_type": service.name, "available_slots": available[:10]}


def book_appointment(user, vehicle_id: int, service_type_id: int, scheduled_at_iso: str) -> dict:
    """Create a pending appointment. Requires the user to own the vehicle."""
    try:
        vehicle = Vehicle.objects.get(pk=vehicle_id)
        service = ServiceType.objects.get(pk=service_type_id)
    except (Vehicle.DoesNotExist, ServiceType.DoesNotExist) as e:
        return {"error": str(e)}

    if not user_owns_vehicle(user, vehicle):
        raise PermissionDenied("You can only book appointments for your own vehicles.")

    try:
        scheduled_at = datetime.fromisoformat(scheduled_at_iso)
        if timezone.is_naive(scheduled_at):
            scheduled_at = timezone.make_aware(scheduled_at)
    except ValueError:
        return {"error": "scheduled_at_iso must be a valid ISO-8601 datetime string."}

    if scheduled_at <= timezone.now():
        return {"error": "Cannot book an appointment in the past."}

    if Appointment.objects.filter(scheduled_at=scheduled_at).exclude(status=Appointment.Status.CANCELLED).exists():
        return {"error": "That slot was just taken. Please choose another."}

    appointment = Appointment.objects.create(
        vehicle=vehicle,
        service_type=service,
        scheduled_at=scheduled_at,
        status=Appointment.Status.PENDING,
        created_by_agent=True,
    )
    return {
        "success": True,
        "appointment_id": appointment.id,
        "status": appointment.status,
        "scheduled_at": appointment.scheduled_at.isoformat(),
    }


def cancel_appointment(user, appointment_id: int, confirm: bool = False) -> dict:
    """Cancel an appointment. Destructive action — requires confirm=True
    (SRS 6.4 Destructive Action Confirmation)."""
    try:
        appointment = Appointment.objects.get(pk=appointment_id)
    except Appointment.DoesNotExist:
        return {"error": f"Appointment {appointment_id} not found."}

    if not user_owns_vehicle(user, appointment.vehicle):
        raise PermissionDenied("You cannot cancel this appointment.")

    if not confirm:
        return {
            "requires_confirmation": True,
            "message": f"Please confirm you want to cancel the appointment on "
                       f"{appointment.scheduled_at:%Y-%m-%d %H:%M}. Call this tool again with confirm=true.",
        }

    appointment.status = Appointment.Status.CANCELLED
    appointment.save()
    return {"success": True, "appointment_id": appointment.id, "status": appointment.status}


# ---------------------------------------------------------------------------
# JSON schemas exposed to the LLM for tool calling
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "get_overdue_services",
        "description": "Get the list of maintenance services that are currently overdue for a specific vehicle owned by the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vehicle_id": {"type": "integer", "description": "The ID of the vehicle to check."},
            },
            "required": ["vehicle_id"],
        },
    },
    {
        "name": "check_available_slots",
        "description": "Check available appointment time slots for a given service type over the next N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_type_id": {"type": "integer", "description": "The ID of the service type."},
                "days_ahead": {"type": "integer", "description": "How many days ahead to search (1-30). Defaults to 7."},
            },
            "required": ["service_type_id"],
        },
    },
    {
        "name": "book_appointment",
        "description": "Book a maintenance appointment for one of the user's own vehicles at a specific time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vehicle_id": {"type": "integer"},
                "service_type_id": {"type": "integer"},
                "scheduled_at_iso": {"type": "string", "description": "ISO-8601 datetime, e.g. 2026-10-01T10:00:00"},
            },
            "required": ["vehicle_id", "service_type_id", "scheduled_at_iso"],
        },
    },
    {
        "name": "cancel_appointment",
        "description": "Cancel an existing appointment. This is destructive: the first call without confirm=true will only return a confirmation prompt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "integer"},
                "confirm": {"type": "boolean", "description": "Set true only after the user has explicitly confirmed."},
            },
            "required": ["appointment_id"],
        },
    },
]

TOOL_FUNCTIONS = {
    "get_overdue_services": get_overdue_services,
    "check_available_slots": check_available_slots,
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
}
