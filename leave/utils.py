"""
Utility functions for the leave management system.
"""

from datetime import timedelta
from django.utils import timezone

from .models import Leave


def is_user_on_leave(user, date):
    """
    Check if a user is on approved leave for a specific date.
    
    Args:
        user: The user to check
        date: The date to check (datetime.date object)
    
    Returns:
        Leave object if user is on leave, None otherwise
    """
    try:
        return Leave.objects.get(
            user=user,
            status=Leave.Status.APPROVED,
            start_date__lte=date,
            end_date__gte=date,
        )
    except Leave.DoesNotExist:
        return None


def get_leave_days_count(start_date, end_date):
    """
    Calculate the number of days for a leave period.
    
    Args:
        start_date: Start date (datetime.date)
        end_date: End date (datetime.date)
    
    Returns:
        Number of days (inclusive)
    """
    if start_date > end_date:
        return 0
    return (end_date - start_date).days + 1


def get_upcoming_leaves(user, days=30):
    """
    Get upcoming approved leaves for a user.
    
    Args:
        user: The user to check
        days: Number of days ahead to look
    
    Returns:
        QuerySet of upcoming leaves
    """
    future_date = timezone.now().date() + timedelta(days=days)
    
    return Leave.objects.filter(
        user=user,
        status=Leave.Status.APPROVED,
        start_date__gte=timezone.now().date(),
        start_date__lte=future_date,
    ).order_by("start_date")


def get_leave_statistics(user=None):
    """
    Get leave statistics for a user or all users.
    
    Args:
        user: Specific user (optional)
    
    Returns:
        Dictionary with statistics
    """
    queryset = Leave.objects.all()
    if user:
        queryset = queryset.filter(user=user)
    
    return {
        "total": queryset.count(),
        "pending": queryset.filter(status=Leave.Status.PENDING).count(),
        "approved": queryset.filter(status=Leave.Status.APPROVED).count(),
        "rejected": queryset.filter(status=Leave.Status.REJECTED).count(),
    }


def can_request_leave(user, start_date, end_date):
    """
    Check if a user can request leave for the given dates.
    
    Args:
        user: The user making the request
        start_date: Start date
        end_date: End date
    
    Returns:
        Tuple of (can_request, reason)
    """
    # Check for overlapping leave requests
    overlapping_leaves = Leave.objects.filter(
        user=user,
        status__in=[Leave.Status.PENDING, Leave.Status.APPROVED],
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    
    if overlapping_leaves.exists():
        return False, "You already have a leave request that overlaps with these dates."
    
    # Check if dates are in the past
    today = timezone.now().date()
    if start_date < today or end_date < today:
        return False, "Leave dates cannot be in the past."
    
    if end_date < start_date:
        return False, "End date must be on or after start date."
    
    return True, ""
