"""
Authentication utility functions for the accounts app.
"""

from django.contrib.auth import login
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login for security auditing."""
    logger.info(
        f"User {user.get_username()} (ID: {user.id}) logged in from "
        f"IP: {get_client_ip(request)} at {timezone.now()}"
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout for security auditing."""
    if user:
        logger.info(
            f"User {user.get_username()} (ID: {user.id}) logged out from "
            f"IP: {get_client_ip(request)} at {timezone.now()}"
        )


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    Takes into account proxies and load balancers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or 'unknown'


def is_safe_redirect_url(url, allowed_hosts=None):
    """
    Validate that a redirect URL is safe to prevent open redirect attacks.
    """
    from django.utils.http import url_has_allowed_host_and_scheme
    
    if allowed_hosts is None:
        from django.conf import settings
        allowed_hosts = set(settings.ALLOWED_HOSTS) | {'localhost', '127.0.0.1'}
    
    return url_has_allowed_host_and_scheme(url, allowed_hosts=allowed_hosts)


def get_user_session_info(request):
    """
    Get information about the user's current session for security monitoring.
    """
    if not request.user.is_authenticated:
        return None
    
    session = request.session
    return {
        'user_id': request.user.id,
        'username': request.user.get_username(),
        'session_key': session.session_key,
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],  # Truncate for safety
        'last_activity': session.get('last_activity'),
    }
