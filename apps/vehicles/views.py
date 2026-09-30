from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404

from apps.authentication.permissions import role_required, user_owns_vehicle
from .forms import VehicleForm, AppointmentForm
from .models import Vehicle, Appointment


@login_required
def vehicle_list_view(request):
    if request.user.role in ("ADMIN", "MANAGER"):
        vehicles = Vehicle.objects.all()
    else:
        vehicles = Vehicle.objects.filter(owner=request.user)
    return render(request, "vehicles/vehicle_list.html", {"vehicles": vehicles})


@login_required
def vehicle_create_view(request):
    if request.method == "POST":
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.owner = request.user
            vehicle.save()
            messages.success(request, "Vehicle added.")
            return redirect("vehicles:vehicle_list")
    else:
        form = VehicleForm()
    return render(request, "vehicles/vehicle_form.html", {"form": form})


@login_required
def vehicle_detail_view(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if not user_owns_vehicle(request.user, vehicle):
        raise PermissionDenied("You do not have access to this vehicle.")
    records = vehicle.maintenance_records.all()
    appointments = vehicle.appointments.all()
    return render(
        request, "vehicles/vehicle_detail.html",
        {"vehicle": vehicle, "records": records, "appointments": appointments},
    )


@login_required
def appointment_list_view(request):
    user = request.user
    if user.role in ("ADMIN", "MANAGER"):
        appointments = Appointment.objects.all()
    elif user.is_technician():
        appointments = Appointment.objects.filter(technician=user)
    else:
        appointments = Appointment.objects.filter(vehicle__owner=user)
    return render(request, "vehicles/appointment_list.html", {"appointments": appointments})


@login_required
def appointment_create_view(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            if not user_owns_vehicle(request.user, appointment.vehicle):
                raise PermissionDenied("You can only book appointments for your own vehicles.")
            appointment.save()
            messages.success(request, "Appointment requested.")
            return redirect("vehicles:appointment_list")
    else:
        form = AppointmentForm(user=request.user)
    return render(request, "vehicles/appointment_form.html", {"form": form})


@login_required
@role_required("ADMIN", "MANAGER")
def appointment_confirm_view(request, pk):
    """Destructive/state-changing action -> requires explicit POST confirmation
    per SRS 6 'Destructive Action Confirmation' governance rule."""
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save()
        messages.success(request, "Appointment confirmed.")
        return redirect("vehicles:appointment_list")
    return render(request, "vehicles/appointment_confirm.html", {"appointment": appointment})


@login_required
def appointment_cancel_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if not user_owns_vehicle(request.user, appointment.vehicle):
        raise PermissionDenied("You cannot cancel this appointment.")
    if request.method == "POST":
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        messages.success(request, "Appointment cancelled.")
        return redirect("vehicles:appointment_list")
    return render(request, "vehicles/appointment_cancel_confirm.html", {"appointment": appointment})
