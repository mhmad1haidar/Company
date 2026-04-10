"""
Attendance business logic (keep views thin; call these functions from views, tasks, commands).
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils import timezone

from attendance.exceptions import CheckOutWithoutCheckInError, DuplicateAttendanceError
from attendance.models import Attendance
from accounts.models import Notification

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

User = get_user_model()


def _late_cutoff() -> time:
    return getattr(settings, "ATTENDANCE_LATE_CUTOFF", time(9, 0))


def _status_for_check_in(at: datetime) -> str:
    local_time = timezone.localtime(at).time()
    if local_time > _late_cutoff():
        return Attendance.Status.LATE
    return Attendance.Status.PRESENT


def calculate_hours(attendance: Attendance) -> Decimal | None:
    """
    Derive working hours from check_in / check_out (does not persist).

    Returns None if times are missing or invalid.
    """
    if (
        not attendance.check_in
        or not attendance.check_out
        or attendance.check_out < attendance.check_in
    ):
        return None
    delta = attendance.check_out - attendance.check_in
    hours = delta.total_seconds() / 3600
    return Decimal(str(round(hours, 2)))


def _get_or_create_attendance_for_day(
    user: AbstractUser,
    day: date,
    *,
    defaults: dict,
) -> tuple[Attendance, bool]:
    """
    get_or_create with lock; retries on IntegrityError from concurrent inserts.
    """
    try:
        return Attendance.objects.select_for_update().get_or_create(
            user=user,
            date=day,
            defaults=defaults,
        )
    except IntegrityError:
        record = Attendance.objects.select_for_update().get(user=user, date=day)
        return record, False


@transaction.atomic
def check_in(user: AbstractUser, at: datetime | None = None) -> Attendance:
    """
    Record one check-in per user per calendar day.

    If the user already checked in today, returns the existing row (idempotent).
    Late if local check-in time is after ATTENDANCE_LATE_CUTOFF (default 09:00).

    Raises:
        DuplicateAttendanceError: Rare integrity failure while saving the row.
    """
    now = at or timezone.now()
    day = timezone.localdate(now)
    status = _status_for_check_in(now)

    record, _created = _get_or_create_attendance_for_day(
        user,
        day,
        defaults={"check_in": now, "status": status},
    )

    if record.check_in is not None:
        return record

    record.check_in = now
    record.status = status
    try:
        record.save(update_fields=["check_in", "status", "updated_at"])
    except IntegrityError as e:
        raise DuplicateAttendanceError() from e
    
    # Notify user if check-in is late
    if status == Attendance.Status.LATE:
        Notification.objects.create(
            recipient=user,
            notification_type=Notification.NotificationType.ATTENDANCE_LATE,
            title="Late Check-in",
            message=f"You checked in at {timezone.localtime(now).strftime('%H:%M')}, which is after the late cutoff time.",
            link="/attendance/dashboard/"
        )
    
    return record


@transaction.atomic
def check_out(user: AbstractUser, at: datetime | None = None) -> Attendance:
    """
    Record check-out for today. Requires an existing check-in for the same day.

    Idempotent: if already checked out, returns the existing row unchanged.
    Working hours are stored on the row via model save (uses calculate_hours).

    Raises:
        CheckOutWithoutCheckInError: No row for today or check-in missing.
    """
    now = at or timezone.now()
    day = timezone.localdate(now)

    record = (
        Attendance.objects.select_for_update()
        .filter(user=user, date=day)
        .first()
    )
    if record is None or record.check_in is None:
        raise CheckOutWithoutCheckInError()

    if record.check_out is not None:
        return record

    record.check_out = now
    try:
        record.save(update_fields=["check_out", "updated_at"])
    except IntegrityError as e:
        raise DuplicateAttendanceError() from e
    return record


def mark_absent_for_missing_users(
    *,
    for_date: date | None = None,
    users: QuerySet | None = None,
) -> int:
    """
    For a calendar day, mark users as ABSENT when they have no check-in.

    Creates an Attendance row if missing. Does not change rows that already
    have a check-in. By default only active, non-superuser accounts are considered.

    Returns how many rows were created or had status set to ABSENT.
    """
    target_date = for_date or timezone.localdate()
    if users is None:
        user_qs = User.objects.filter(is_active=True).exclude(is_superuser=True)
    else:
        user_qs = users

    count = 0
    for user in user_qs.iterator():
        with transaction.atomic():
            record = (
                Attendance.objects.select_for_update()
                .filter(user=user, date=target_date)
                .first()
            )
            if record is None:
                try:
                    Attendance.objects.create(
                        user=user,
                        date=target_date,
                        status=Attendance.Status.ABSENT,
                    )
                    count += 1
                except IntegrityError:
                    # Another worker created the row; treat as no-op for this counter.
                    continue
            elif record.check_in is None:
                if record.status != Attendance.Status.ABSENT:
                    record.status = Attendance.Status.ABSENT
                    record.save(update_fields=["status", "updated_at"])
                    count += 1
                    # Notify user about absence
                    Notification.objects.create(
                        recipient=user,
                        notification_type=Notification.NotificationType.ATTENDANCE_ABSENT,
                        title="Marked Absent",
                        message=f"You were marked absent on {target_date.strftime('%B %d, %Y')} due to no check-in.",
                        link="/attendance/dashboard/"
                    )

    return count
