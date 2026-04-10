"""
Attendance system services with leave integration.
"""

from django.utils import timezone
from django.db import transaction

from .exceptions import OnLeaveError, DuplicateAttendanceError, CheckOutWithoutCheckInError
from .models import Attendance
from leave.utils import is_user_on_leave


def check_in(user):
    """
    Check in a user, preventing check-in if they're on approved leave.
    Allows multiple check-ins per day for breaks/permissions.
    
    Args:
        user: The user to check in
        
    Raises:
        OnLeaveError: If user is on approved leave
    """
    today = timezone.localdate()
    
    # Check if user is on approved leave
    leave = is_user_on_leave(user, today)
    if leave:
        raise OnLeaveError(
            f"You cannot check in while on approved leave from {leave.start_date} to {leave.end_date}."
        )
    
    # Create attendance record (allows multiple per day for breaks/permissions)
    Attendance.objects.create(
        user=user,
        date=today,
        check_in=timezone.now(),
    )


def check_out(user):
    """
    Check out a user.
    Allows multiple check-outs per day - checks out the most recent unchecked-in attendance record.
    
    Args:
        user: The user to check out
        
    Raises:
        CheckOutWithoutCheckInError: If user hasn't checked in today without checking out
    """
    today = timezone.localdate()
    
    # Get the most recent attendance record that hasn't been checked out
    attendance = Attendance.objects.filter(
        user=user, 
        date=today,
        check_out__isnull=True
    ).order_by('-check_in').first()
    
    if not attendance:
        raise CheckOutWithoutCheckInError("You don't have any active check-ins to check out from.")
    
    # Update check-out time
    attendance.check_out = timezone.now()
    attendance.save()


def get_attendance_status(user, date=None):
    """
    Get attendance status for a user on a specific date.
    
    Args:
        user: The user to check
        date: Date to check (defaults to today)
        
    Returns:
        Dictionary with attendance and leave status
    """
    if date is None:
        date = timezone.localdate()
    
    # Check attendance
    try:
        attendance = Attendance.objects.get(user=user, date=date)
        attendance_status = {
            "checked_in": bool(attendance.check_in),
            "checked_out": bool(attendance.check_out),
            "check_in_time": attendance.check_in,
            "check_out_time": attendance.check_out,
        }
    except Attendance.DoesNotExist:
        attendance_status = {
            "checked_in": False,
            "checked_out": False,
            "check_in_time": None,
            "check_out_time": None,
        }
    
    # Check leave status
    leave = is_user_on_leave(user, date)
    leave_status = {
        "on_leave": bool(leave),
        "leave": leave,
    }
    
    return {
        **attendance_status,
        **leave_status,
        "date": date,
        "can_check_in": not attendance_status["checked_in"] and not leave_status["on_leave"],
        "can_check_out": attendance_status["checked_in"] and not attendance_status["checked_out"],
    }


def get_daily_attendance_summary(date=None):
    """
    Get daily attendance summary with leave information.
    
    Args:
        date: Date to check (defaults to today)
        
    Returns:
        Dictionary with attendance statistics
    """
    if date is None:
        date = timezone.localdate()
    
    # Get all attendance records for the date
    attendances = Attendance.objects.filter(date=date).select_related("user")
    
    # Get all users on approved leave for the date
    from accounts.models import User
    from leave.models import Leave
    
    users_on_leave = Leave.objects.filter(
        status=Leave.Status.APPROVED,
        start_date__lte=date,
        end_date__gte=date,
    ).values_list("user_id", flat=True)
    
    total_users = User.objects.filter(is_active=True).count()
    present_count = attendances.filter(check_in__isnull=False).count()
    checked_out_count = attendances.filter(check_out__isnull=False).count()
    on_leave_count = len(users_on_leave)
    absent_count = total_users - present_count - on_leave_count
    
    return {
        "date": date,
        "total_users": total_users,
        "present": present_count,
        "checked_out": checked_out_count,
        "on_leave": on_leave_count,
        "absent": absent_count,
        "attendance_rate": (present_count / total_users * 100) if total_users > 0 else 0,
    }
