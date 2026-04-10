import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def leave_attachment_path(instance, filename):
    """Generate upload path for leave attachments: leave_attachments/user_id_username/YYYY/MM/filename"""
    user_id = instance.user.id
    username = instance.user.username
    year = timezone.now().year
    month = timezone.now().month
    # Get file extension
    ext = os.path.splitext(filename)[1]
    # Create safe filename
    safe_filename = f"leave_{instance.id if instance.id else 'new'}{ext}"
    return f'leave_attachments/{user_id}_{username}/{year:04d}/{month:02d}/{safe_filename}'


class LeaveType(models.Model):
    """
    Reference data for leave categories (normalized lookup).

    Use a table rather than free text so reporting and policies stay consistent.
    """

    code = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Leave type"
        verbose_name_plural = "Leave types"

    def __str__(self) -> str:
        return self.name


class Leave(models.Model):
    """Time-off request: one row per request (dates may span multiple days)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leaves",
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="leaves",
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reason = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to=leave_attachment_path,
        blank=True,
        null=True,
        help_text="Upload supporting documents (optional)"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leave_approvals",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} ({self.start_date}–{self.end_date})"

    def clean(self) -> None:
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": "End date must be on or after start date."},
            )

    def save(self, *args, **kwargs):
        self.full_clean(exclude=[])
        super().save(*args, **kwargs)

    @property
    def status_color(self):
        """Return Bootstrap color class for status."""
        colors = {
            self.Status.PENDING: "warning",
            self.Status.APPROVED: "success",
            self.Status.REJECTED: "danger",
        }
        return colors.get(self.status, "secondary")
