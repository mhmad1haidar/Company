from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Attendance(models.Model):
    """
    One row per user per calendar day.

    `total_hours` is derived from `check_in` / `check_out` and stored for reporting
    and indexing (recalculated on save when both timestamps are set).
    """

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField(db_index=True)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    total_hours = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text="Computed from check_in and check_out when both are set.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-check_in"]
        constraints = []
        indexes = [
            models.Index(fields=["date", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} @ {self.date}"

    def clean(self) -> None:
        super().clean()
        if self.check_out and not self.check_in:
            raise ValidationError(
                {"check_out": "Check-out cannot be set without a check-in time."},
            )
        if self.check_in and self.check_out and self.check_out < self.check_in:
            raise ValidationError(
                {"check_out": "Check-out must be on or after check-in."},
            )

    def _recompute_total_hours(self) -> None:
        # Delegate to service so hours logic lives in one place.
        from attendance.services.attendance_service import calculate_hours

        self.total_hours = calculate_hours(self)

    def save(self, *args, **kwargs):
        self.full_clean(exclude=[])
        self._recompute_total_hours()
        super().save(*args, **kwargs)

    @property
    def status_color(self):
        """Return Bootstrap color class for status."""
        colors = {
            self.Status.PRESENT: "success",
            self.Status.ABSENT: "danger", 
            self.Status.LATE: "warning",
        }
        return colors.get(self.status, "secondary")

    @property
    def is_late(self):
        """Check if attendance is marked as late."""
        return self.status == self.Status.LATE
