from decimal import Decimal

from django.db import models

from accounts.models import User


class Car(models.Model):
    FUEL_TYPE_CHOICES = (
        ("diesel", "Diesel"),
        ("petrol", "Petrol"),
        ("electric", "Electric"),
    )

    STATUS_CHOICES = (
        ("available", "Available"),
        ("assigned", "Assigned"),
        ("maintenance", "Maintenance"),
        ("out_of_service", "Out of service"),
    )

    plate_number = models.CharField(max_length=20, unique=True)
    brand = models.CharField(max_length=200, blank=True, default="")
    model = models.CharField(max_length=200, blank=True, default="")
    year = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=50, blank=True, default="")

    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES, blank=True, default="petrol")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")

    assigned_employee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cars",
    )

    insurance_expiry = models.DateField(null=True, blank=True)
    inspection_expiry = models.DateField(null=True, blank=True)
    registration_expiry = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        parts = [self.brand.strip(), self.model.strip()]
        title = " ".join([p for p in parts if p])
        if not title:
            title = self.model or "Car"
        return f"{self.plate_number} ({title})"


class MaintenanceHistory(models.Model):
    MAINTENANCE_TYPE_CHOICES = (
        ("inspection", "Inspection"),
        ("repair", "Repair"),
        ("service", "Service"),
        ("other", "Other"),
    )

    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="maintenance_history")
    date = models.DateField()
    type = models.CharField(max_length=30, choices=MAINTENANCE_TYPE_CHOICES)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.car.plate_number} - {self.type} on {self.date}"


class FuelLog(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="fuel_logs")
    date = models.DateField()
    liters = models.FloatField()
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.car.plate_number} fuel on {self.date}"


class CarUsage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="usage_history")
    intervention = models.ForeignKey("interventions.Intervention", on_delete=models.CASCADE, related_name="car_usage", null=True, blank=True)
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="car_usage")
    date = models.DateField()

    class Meta:
        ordering = ["-date"]
        unique_together = ("car", "intervention", "employee", "date")

    def __str__(self) -> str:
        return f"{self.car.plate_number} used on {self.date}"
