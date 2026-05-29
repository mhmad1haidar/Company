import logging
import threading

from django.conf import settings
from django.db.models import Q
from django.urls import reverse

from accounts.models import User
from company.email_delivery import send_email
from .models import Leave


logger = logging.getLogger(__name__)


def _display_name(user):
    return user.get_full_name() or user.get_username()


def _absolute_url(path):
    base_url = getattr(settings, "SITE_URL", "").rstrip("/")
    return f"{base_url}{path}" if base_url else path


def _admin_recipients():
    users = User.objects.filter(
        Q(is_superuser=True)
        | Q(is_staff=True)
        | Q(role__in=[User.Role.ADMIN, User.Role.MANAGER]),
        is_active=True,
    ).exclude(email="")
    return list(users.values_list("email", flat=True).distinct())


def _send(subject, message, recipients):
    recipients = [email for email in dict.fromkeys(recipients) if email]
    if not recipients:
        return 0

    def send_in_background():
        try:
            send_email(
                subject,
                message,
                recipients,
            )
        except Exception:
            logger.exception("Could not send leave email to %s", ", ".join(recipients))

    threading.Thread(target=send_in_background).start()
    return len(recipients)


def _send_sync(subject, message, recipients):
    recipients = [email for email in dict.fromkeys(recipients) if email]
    if not recipients:
        return 0
    try:
        return send_email(
            subject,
            message,
            recipients,
        )
    except Exception:
        logger.exception("Could not send leave email to %s", ", ".join(recipients))
        return 0


def send_leave_request_submitted_email(leave):
    requester = _display_name(leave.user)
    admin_url = _absolute_url(reverse("leave:leave_admin_detail", args=[leave.pk]))
    subject = f"New leave request from {requester}"
    message = (
        f"A new leave request has been submitted.\n\n"
        f"Employee: {requester}\n"
        f"Email: {leave.user.email or '-'}\n"
        f"Leave type: {leave.leave_type.name}\n"
        f"Dates: {leave.start_date} to {leave.end_date}\n"
        f"Status: {leave.get_status_display()}\n"
        f"Reason: {leave.reason or '-'}\n\n"
        f"Review request: {admin_url}"
    )
    return _send(subject, message, _admin_recipients())


def send_leave_decision_email(leave):
    if not leave.user.email:
        return 0

    status_label = leave.get_status_display()
    subject = f"Your leave request was {status_label.lower()}"
    detail_url = _absolute_url(reverse("leave:leave_detail", args=[leave.pk]))
    approver = _display_name(leave.approved_by) if leave.approved_by else "-"
    message = (
        f"Your leave request status has been updated.\n\n"
        f"Leave type: {leave.leave_type.name}\n"
        f"Dates: {leave.start_date} to {leave.end_date}\n"
        f"Status: {status_label}\n"
        f"Reviewed by: {approver}\n\n"
        f"View request: {detail_url}"
    )
    return _send(subject, message, [leave.user.email])
