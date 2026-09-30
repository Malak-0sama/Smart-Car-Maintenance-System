from django import forms
from .models import Vehicle, Appointment


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ["make", "model", "year", "vin", "license_plate", "current_mileage_km"]


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["vehicle", "service_type", "scheduled_at", "notes"]
        widgets = {
            "scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and user.is_customer():
            self.fields["vehicle"].queryset = Vehicle.objects.filter(owner=user)
