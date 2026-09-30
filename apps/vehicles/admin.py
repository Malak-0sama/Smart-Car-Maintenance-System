from django.contrib import admin
from .models import Vehicle, ServiceType, TechnicianProfile, SparePart, Appointment, AppointmentPart, MaintenanceRecord


class AppointmentPartInline(admin.TabularInline):
    model = AppointmentPart
    extra = 1


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("__str__", "owner", "current_mileage_km")
    search_fields = ("vin", "license_plate", "make", "model")


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "recommended_interval_km", "recommended_interval_months", "base_price")


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "specialty", "is_available")


@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "stock_quantity", "unit_price")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "service_type", "technician", "scheduled_at", "status", "created_by_agent")
    list_filter = ("status", "created_by_agent")
    inlines = [AppointmentPartInline]


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "service_type", "performed_at", "mileage_at_service", "cost")
