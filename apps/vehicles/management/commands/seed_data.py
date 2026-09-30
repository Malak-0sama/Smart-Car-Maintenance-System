"""
Usage: python manage.py seed_data
Populates the DB with realistic demo data for the evaluation/demo session
(SRS 12: 'PostgreSQL Database dump/migrations script populated with
realistic scenario data').
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.authentication.models import CustomUser
from apps.vehicles.models import (
    Vehicle, ServiceType, TechnicianProfile, SparePart,
    Appointment, MaintenanceRecord,
)


class Command(BaseCommand):
    help = "Seed the database with demo users, vehicles, and service history."

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        admin, _ = CustomUser.objects.get_or_create(
            username="admin", defaults={"email": "admin@autocare.com", "role": "ADMIN", "is_staff": True, "is_superuser": True}
        )
        admin.set_password("admin12345")
        admin.save()

        manager, _ = CustomUser.objects.get_or_create(
            username="manager1", defaults={"email": "manager1@autocare.com", "role": "MANAGER"}
        )
        manager.set_password("manager12345")
        manager.save()

        tech_user, _ = CustomUser.objects.get_or_create(
            username="tech1", defaults={"email": "tech1@autocare.com", "role": "TECHNICIAN"}
        )
        tech_user.set_password("tech12345")
        tech_user.save()
        TechnicianProfile.objects.get_or_create(user=tech_user, defaults={"specialty": "Brakes & Suspension"})

        customer, _ = CustomUser.objects.get_or_create(
            username="customer1", defaults={"email": "customer1@example.com", "role": "CUSTOMER"}
        )
        customer.set_password("customer12345")
        customer.save()

        services = [
            ("Oil Change", 5000, 6, 40.00),
            ("Brake Inspection", 15000, 12, 60.00),
            ("Tire Rotation", 10000, 6, 30.00),
            ("Full Inspection", 20000, 12, 90.00),
        ]
        service_objs = {}
        for name, km, months, price in services:
            obj, _ = ServiceType.objects.get_or_create(
                name=name, defaults={
                    "recommended_interval_km": km,
                    "recommended_interval_months": months,
                    "base_price": price,
                }
            )
            service_objs[name] = obj

        SparePart.objects.get_or_create(name="Oil Filter", sku="OF-001", defaults={"stock_quantity": 50, "unit_price": 8.5})
        SparePart.objects.get_or_create(name="Brake Pads (set)", sku="BP-002", defaults={"stock_quantity": 30, "unit_price": 45.0})

        vehicle, _ = Vehicle.objects.get_or_create(
            owner=customer, vin="1HGCM82633A004352", defaults={
                "make": "Toyota", "model": "Corolla", "year": 2019,
                "license_plate": "CAI-1234", "current_mileage_km": 62000,
            }
        )

        # Overdue oil change (last one 8 months / 9000km ago -> triggers agent)
        MaintenanceRecord.objects.get_or_create(
            vehicle=vehicle, service_type=service_objs["Oil Change"],
            performed_at=timezone.now() - timedelta(days=240),
            defaults={"mileage_at_service": 53000, "cost": 40.0, "technician": tech_user},
        )

        Appointment.objects.get_or_create(
            vehicle=vehicle, service_type=service_objs["Tire Rotation"],
            scheduled_at=timezone.now() + timedelta(days=3, hours=10),
            defaults={"status": Appointment.Status.PENDING},
        )

        self.stdout.write(self.style.SUCCESS(
            "Seed complete. Login as customer1/customer12345, manager1/manager12345, "
            "tech1/tech12345, or admin/admin12345."
        ))
