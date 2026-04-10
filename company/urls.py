from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import RedirectView

from . import hr_admin  # noqa: F401 — register admin site branding
from ajax_test_view import ajax_test


urlpatterns = [
    path("", RedirectView.as_view(pattern_name="accounts:dashboard", permanent=False)),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("attendance/", include("attendance.urls", namespace="attendance")),
    path("leave/", include("leave.urls")),
    path("fleet/", include("fleet.urls")),
    path("interventions/", include("interventions.urls")),
    path("assignments/", include("assignments.urls")),
    path("warehouse/", include("warehouse.urls")),
    path("api/v1/", include("company.api_urls")),
    path("ajax-test/", ajax_test, name="ajax_test"),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
