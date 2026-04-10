"""
DRF wrapper: maps domain exceptions to HTTP responses.
"""

from rest_framework.views import exception_handler as drf_exception_handler

from attendance.exceptions import (
    AttendanceServiceError,
    CheckOutWithoutCheckInError,
    DuplicateAttendanceError,
)


def custom_exception_handler(exc, context):
    if isinstance(exc, DuplicateAttendanceError):
        return _attendance_response(exc, 409)
    if isinstance(exc, CheckOutWithoutCheckInError):
        return _attendance_response(exc, 400)
    if isinstance(exc, AttendanceServiceError):
        return _attendance_response(exc, 400)
    return drf_exception_handler(exc, context)


def _attendance_response(exc: AttendanceServiceError, http_status: int):
    from rest_framework.response import Response

    return Response(
        {"detail": str(exc), "code": getattr(exc, "code", "attendance_error")},
        status=http_status,
    )
