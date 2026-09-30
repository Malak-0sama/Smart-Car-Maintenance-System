from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model implementing Role-Based Access Control (RBAC)
    as required by SRS section 3.2.

    Roles:
      - ADMIN:      full system access, manages technicians & service catalog
      - MANAGER:    approves appointments, manages spare-parts inventory
      - TECHNICIAN: views assigned appointments, updates job status
      - CUSTOMER:   owns vehicles, books appointments, uses the AI agent
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        MANAGER = "MANAGER", "Manager"
        TECHNICIAN = "TECHNICIAN", "Technician"
        CUSTOMER = "CUSTOMER", "Customer"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_manager(self):
        return self.role == self.Role.MANAGER

    def is_technician(self):
        return self.role == self.Role.TECHNICIAN

    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    def __str__(self):
        return f"{self.username} ({self.role})"
