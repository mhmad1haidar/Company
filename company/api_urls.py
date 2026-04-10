from django.urls import include, path

urlpatterns = [
    path("accounts/", include("accounts.api.urls")),
    path("attendance/", include("attendance.api.urls")),
    path("leave/", include("leave.api.urls")),
]
