from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class ModuleAccessMiddleware:
    """Block direct URL access to modules hidden from the current user."""

    MODULE_PATHS = (
        ("/accounts/employees/", "employees"),
        ("/accounts/messages/", "messages"),
        ("/accounts/announcements/", "announcements"),
        ("/attendance/", "attendance"),
        ("/leave/", "leave"),
        ("/warehouse/", "warehouse"),
        ("/fleet/", "fleet"),
        ("/assignments/", "assignments"),
        ("/interventions/sites-map/", "sites_map"),
        ("/interventions/", "interventions"),
    )
    ALWAYS_ALLOWED_PREFIXES = (
        "/accounts/dashboard/",
        "/accounts/profile/",
        "/accounts/settings/",
        "/accounts/logout/",
        "/accounts/toggle-dark-mode/",
        "/accounts/notifications/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            if self._is_always_allowed(request.path_info):
                return self.get_response(request)
            module = self._module_for_path(request.path_info)
            if module and not self._has_access(user, module):
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    raise PermissionDenied("You do not have access to that section.")
                messages.error(request, "You do not have access to that section.")
                return redirect("accounts:dashboard")
        return self.get_response(request)

    def _is_always_allowed(self, path):
        return any(path.startswith(prefix) for prefix in self.ALWAYS_ALLOWED_PREFIXES)

    def _module_for_path(self, path):
        for prefix, module in self.MODULE_PATHS:
            if path.startswith(prefix):
                return module
        return None

    def _has_access(self, user, module):
        checker = getattr(user, "has_module_access", None)
        if callable(checker):
            return checker(module)
        return user.is_superuser or user.is_staff
