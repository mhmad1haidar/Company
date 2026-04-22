from .models import Message, Announcement
from django.utils import timezone
from django.db.models import Q


def notification_counts(request):
    """
    Context processor to provide notification counts for messages and announcements
    """
    if not request.user.is_authenticated:
        return {
            'unread_message_count': 0,
            'active_announcement_count': 0,
        }

    # Count unread messages
    unread_message_count = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    # Count active announcements
    active_announcement_count = Announcement.objects.filter(
        is_active=True,
        start_date__lte=timezone.now()
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
    ).count()

    return {
        'unread_message_count': unread_message_count,
        'active_announcement_count': active_announcement_count,
    }
