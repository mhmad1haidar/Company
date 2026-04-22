from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import Certification

User = get_user_model()


class Command(BaseCommand):
    help = 'Check for expiring certifications and send alerts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days before expiry to send alerts (default: 30)',
        )

    def handle(self, *args, **options):
        days_threshold = options['days']
        today = timezone.now().date()
        expiry_threshold = today + timezone.timedelta(days=days_threshold)

        # Find certifications expiring soon
        expiring_certifications = Certification.objects.filter(
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=today,
            is_active=True
        )

        # Find expired certifications
        expired_certifications = Certification.objects.filter(
            expiry_date__lt=today,
            is_active=True
        )

        self.stdout.write(f"Found {expiring_certifications.count()} certifications expiring in {days_threshold} days")
        self.stdout.write(f"Found {expired_certifications.count()} expired certifications")

        # Send alerts for expiring certifications
        for cert in expiring_certifications:
            self.send_expiry_alert(cert, 'expiring_soon', days_threshold)

        # Send alerts for expired certifications
        for cert in expired_certifications:
            self.send_expiry_alert(cert, 'expired', 0)

        self.stdout.write(self.style.SUCCESS('Certification expiry check completed'))

    def send_expiry_alert(self, certification, alert_type, days):
        """Send email alert for certification expiry"""
        user = certification.employee
        email = user.email

        if not email:
            self.stdout.write(self.style.WARNING(f'No email for user {user.username}'))
            return

        if alert_type == 'expiring_soon':
            subject = f'Certification Expiring Soon: {certification.certification_name}'
            message = f'''
Dear {user.get_full_name() or user.username},

Your certification "{certification.certification_name}" will expire in {days} days on {certification.expiry_date}.

Certification Details:
- Name: {certification.certification_name}
- Number: {certification.certification_number}
- Issuing Organization: {certification.issuing_organization}
- Issue Date: {certification.issue_date}
- Expiry Date: {certification.expiry_date}

Please renew your certification before it expires to maintain your professional credentials.

Best regards,
HR Team
'''
        else:  # expired
            subject = f'Certification Expired: {certification.certification_name}'
            message = f'''
Dear {user.get_full_name() or user.username},

Your certification "{certification.certification_name}" expired on {certification.expiry_date}.

Certification Details:
- Name: {certification.certification_name}
- Number: {certification.certification_number}
- Issuing Organization: {certification.issuing_organization}
- Issue Date: {certification.issue_date}
- Expiry Date: {certification.expiry_date}

Please renew your certification as soon as possible.

Best regards,
HR Team
'''

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            self.stdout.write(f'Alert sent to {email} for {certification.certification_name}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email to {email}: {str(e)}'))
