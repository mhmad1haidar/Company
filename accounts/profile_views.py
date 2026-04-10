from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class UserProfileView(LoginRequiredMixin, TemplateView):
    """User profile page."""
    template_name = "accounts/profile.html"


class UserSettingsView(LoginRequiredMixin, TemplateView):
    """User settings page."""
    template_name = "accounts/settings.html"
