from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.vehicles.models import Vehicle, Appointment


def landing_view(request):
    return render(request, "core/landing.html")


@login_required
def dashboard_view(request):
    user = request.user
    context = {"user": user}

    if user.is_customer():
        vehicles = Vehicle.objects.filter(owner=user)
        upcoming = Appointment.objects.filter(
            vehicle__owner=user, scheduled_at__gte=timezone.now()
        ).exclude(status=Appointment.Status.CANCELLED).order_by("scheduled_at")[:5]
        context.update({"vehicles": vehicles, "upcoming_appointments": upcoming})

    elif user.is_technician():
        assigned = Appointment.objects.filter(technician=user).exclude(
            status=Appointment.Status.COMPLETED
        ).order_by("scheduled_at")
        context.update({"assigned_appointments": assigned})

    elif user.role in ("ADMIN", "MANAGER"):
        pending = Appointment.objects.filter(status=Appointment.Status.PENDING).order_by("scheduled_at")
        overdue_count = Vehicle.objects.count()  # simplified KPI; real overdue calc lives in ai_agent.tools
        context.update({
            "pending_appointments": pending,
            "total_vehicles": overdue_count,
            "total_customers": user.__class__.objects.filter(role="CUSTOMER").count(),
        })

    return render(request, "core/dashboard.html", context)
