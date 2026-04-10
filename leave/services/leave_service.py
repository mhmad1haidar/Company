from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from leave.models import Leave, LeaveType

User = get_user_model()


class LeaveService:
    """Approval workflow and invariants for leave requests."""

    @staticmethod
    @transaction.atomic
    def submit(
        *,
        user: User,
        leave_type: LeaveType,
        start_date,
        end_date,
        reason: str = "",
    ) -> Leave:
        return Leave.objects.create(
            user=user,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status=Leave.Status.PENDING,
        )

    @staticmethod
    @transaction.atomic
    def approve(leave: Leave, manager: User) -> Leave:
        leave.status = Leave.Status.APPROVED
        leave.approved_by = manager
        leave.approved_at = timezone.now()
        leave.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
        return leave

    @staticmethod
    @transaction.atomic
    def reject(leave: Leave, manager: User) -> Leave:
        leave.status = Leave.Status.REJECTED
        leave.approved_by = manager
        leave.approved_at = timezone.now()
        leave.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
        return leave
