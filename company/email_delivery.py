import base64
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail


logger = logging.getLogger(__name__)


def _clean_recipients(recipients):
    return [email for email in dict.fromkeys(recipients or []) if email]


def _resend_payload(subject, text, recipients, html=None, attachments=None):
    payload = {
        "from": getattr(settings, "DEFAULT_FROM_EMAIL", "Company Platform <onboarding@resend.dev>"),
        "to": recipients,
        "subject": subject,
        "text": text or "",
    }
    if html:
        payload["html"] = html
    if attachments:
        payload["attachments"] = [
            {
                "filename": item["filename"],
                "content": base64.b64encode(item["content"]).decode("ascii"),
            }
            for item in attachments
        ]
    return payload


def send_email(subject, text, recipients, html=None, attachments=None):
    recipients = _clean_recipients(recipients)
    if not recipients:
        return 0

    resend_api_key = getattr(settings, "RESEND_API_KEY", "")
    if resend_api_key:
        request = Request(
            "https://api.resend.com/emails",
            data=json.dumps(_resend_payload(subject, text, recipients, html, attachments)).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=getattr(settings, "EMAIL_TIMEOUT", 10)) as response:
                response.read()
            return len(recipients)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.exception("Resend email failed with HTTP %s: %s", exc.code, detail)
            return 0
        except URLError:
            logger.exception("Resend email network error")
            return 0

    try:
        if html or attachments:
            message = EmailMultiAlternatives(
                subject=subject,
                body=text or "",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
                to=recipients,
            )
            if html:
                message.attach_alternative(html, "text/html")
            for item in attachments or []:
                message.attach(item["filename"], item["content"], item.get("content_type", "application/octet-stream"))
            return message.send(fail_silently=False)
        return send_mail(
            subject,
            text or "",
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipients,
            fail_silently=False,
        )
    except Exception:
        logger.exception("SMTP email failed to %s", ", ".join(recipients))
        return 0
