import logging
import threading
from html import escape
from io import BytesIO

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import close_old_connections
from django.db.models import Q
from django.urls import reverse

from accounts.models import User
from .models import CorrectiveReport


logger = logging.getLogger(__name__)


def _display_name(user):
    if not user:
        return "-"
    return user.get_full_name() or user.get_username()


def _absolute_url(path):
    base_url = getattr(settings, "SITE_URL", "").rstrip("/")
    return f"{base_url}{path}" if base_url else path


def _supervisor_recipients():
    users = User.objects.filter(
        Q(is_superuser=True)
        | Q(is_staff=True)
        | Q(role__in=[User.Role.ADMIN, User.Role.MANAGER]),
        is_active=True,
    ).exclude(email="")
    return list(users.values_list("email", flat=True).distinct())


def _format_answer(value):
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip()) or "-"
    return str(value) if value not in [None, ""] else "-"


def _build_html(report):
    intervention = report.intervention
    detail_url = _absolute_url(reverse("interventions:corrective-report-detail", args=[report.pk]))
    rows = "".join(
        f"""
        <tr>
            <td style="padding:8px 10px;border:1px solid #dde3ea;font-weight:700;color:#334155;">{escape(label)}</td>
            <td style="padding:8px 10px;border:1px solid #dde3ea;color:#111827;">{escape(_format_answer(value))}</td>
        </tr>
        """
        for label, value in (report.answers or {}).items()
    )
    return f"""
    <div style="font-family:Arial,sans-serif;color:#111827;line-height:1.45;">
        <h2 style="margin:0 0 8px;">New Corrective Report Submitted</h2>
        <p style="margin:0 0 16px;color:#64748b;">A corrective report was submitted by {_display_name(report.reporter)}.</p>
        <table style="border-collapse:collapse;width:100%;margin-bottom:16px;">
            <tr><td style="padding:6px 0;color:#64748b;">Codice NIGIT</td><td style="padding:6px 0;font-weight:700;">{escape(intervention.codice_nigit or "-")}</td></tr>
            <tr><td style="padding:6px 0;color:#64748b;">Intervention</td><td style="padding:6px 0;font-weight:700;">{escape(intervention.nome or "-")}</td></tr>
            <tr><td style="padding:6px 0;color:#64748b;">Client</td><td style="padding:6px 0;font-weight:700;">{escape(intervention.cliente or "-")}</td></tr>
            <tr><td style="padding:6px 0;color:#64748b;">Submitted at</td><td style="padding:6px 0;font-weight:700;">{report.submitted_at or report.created_at}</td></tr>
        </table>
        <h3 style="margin:18px 0 8px;">Questions & Answers</h3>
        <table style="border-collapse:collapse;width:100%;font-size:13px;">
            {rows or '<tr><td style="padding:10px;border:1px solid #dde3ea;">No answers saved.</td></tr>'}
        </table>
        <p style="margin-top:16px;">
            <a href="{escape(detail_url)}" style="color:#1d4ed8;font-weight:700;">Open corrective report</a>
        </p>
    </div>
    """


def _build_text(report):
    intervention = report.intervention
    lines = [
        "New corrective report submitted",
        "",
        f"Codice NIGIT: {intervention.codice_nigit or '-'}",
        f"Intervention: {intervention.nome or '-'}",
        f"Client: {intervention.cliente or '-'}",
        f"Reporter: {_display_name(report.reporter)}",
        f"Submitted at: {report.submitted_at or report.created_at}",
        "",
        "Questions & Answers:",
    ]
    for label, value in (report.answers or {}).items():
        lines.append(f"- {label}: {_format_answer(value)}")
    lines.extend(["", f"Open: {_absolute_url(reverse('interventions:corrective-report-detail', args=[report.pk]))}"])
    return "\n".join(lines)


def _build_pdf(report):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib import colors

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Corrective Report", styles["Title"]),
        Paragraph(f"Codice NIGIT: {escape(report.intervention.codice_nigit or '-')}", styles["Heading2"]),
        Paragraph(f"Reporter: {escape(_display_name(report.reporter))}", styles["Normal"]),
        Paragraph(f"Submitted: {report.submitted_at or report.created_at}", styles["Normal"]),
        Spacer(1, 8),
    ]

    data = [["Question", "Answer"]]
    for label, value in (report.answers or {}).items():
        data.append([
            Paragraph(escape(label), styles["BodyText"]),
            Paragraph(escape(_format_answer(value)), styles["BodyText"]),
        ])
    if len(data) == 1:
        data.append(["No answers", "-"])

    table = Table(data, colWidths=[62 * mm, 106 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef4ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()


def send_corrective_report_submitted_email(report_id):
    recipients = _supervisor_recipients()
    if not recipients:
        return 0

    def send_in_background():
        close_old_connections()
        try:
            report = CorrectiveReport.objects.select_related("intervention", "reporter").get(pk=report_id)
            code = report.intervention.codice_nigit or report.pk
            subject = f"Corrective report submitted - {code}"
            message = EmailMultiAlternatives(
                subject=subject,
                body=_build_text(report),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
                to=recipients,
            )
            message.attach_alternative(_build_html(report), "text/html")
            message.attach(
                f"corrective-report-{code}.pdf",
                _build_pdf(report),
                "application/pdf",
            )
            message.send(fail_silently=False)
        except Exception:
            logger.exception("Could not send corrective report email for report %s", report_id)
        finally:
            close_old_connections()

    threading.Thread(target=send_in_background, daemon=True).start()
    return len(recipients)
