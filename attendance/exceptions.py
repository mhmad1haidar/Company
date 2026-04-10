"""Domain exceptions for attendance operations (API and web layers map these to responses)."""


class AttendanceServiceError(Exception):
    """Base class for predictable attendance business-rule failures."""

    default_message = "An attendance error occurred."
    code = "attendance_error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class DuplicateAttendanceError(AttendanceServiceError):
    """Raised when a second row would violate one attendance record per user per day."""

    default_message = "An attendance record already exists for this user and date."
    code = "duplicate_attendance"


class CheckOutWithoutCheckInError(AttendanceServiceError):
    """Raised when check-out is attempted without a prior check-in for that day."""

    default_message = "Check in is required before check out for this date."
    code = "checkout_without_checkin"


class OnLeaveError(AttendanceServiceError):
    """Raised when check-in is attempted while user is on approved leave."""

    default_message = "Cannot check in while on approved leave."
    code = "on_leave"
