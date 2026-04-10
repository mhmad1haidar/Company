from .attendance_service import (
    calculate_hours,
    check_in,
    check_out,
    mark_absent_for_missing_users,
)

# Import from services.py file
try:
    from ..services import (
        check_in as attendance_check_in,
        check_out as attendance_check_out,
        get_attendance_status,
        get_daily_attendance_summary,
    )
    __all__ = [
        "calculate_hours",
        "check_in",
        "check_out",
        "mark_absent_for_missing_users",
        "attendance_check_in",
        "attendance_check_out",
        "get_attendance_status",
        "get_daily_attendance_summary",
    ]
except ImportError:
    __all__ = [
        "calculate_hours",
        "check_in",
        "check_out",
        "mark_absent_for_missing_users",
    ]
