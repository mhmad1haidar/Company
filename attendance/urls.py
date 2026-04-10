from django.urls import path
from django.views.generic import RedirectView

from . import views
from . import analytics_views

app_name = 'attendance'

urlpatterns = [
    path("", views.AttendanceDashboardView.as_view(), name="attendance_dashboard"),
    path("dashboard/", views.AttendanceDashboardView.as_view(), name="attendance_dashboard"),
    path("check-in/", views.AttendanceCheckInView.as_view(), name="attendance_check_in"),
    path("check-out/", views.AttendanceCheckOutView.as_view(), name="attendance_check_out"),
    path("analytics/", analytics_views.AttendanceAnalyticsView.as_view(), name="attendance_analytics"),
    path("timesheet/", views.TimesheetDownloadView.as_view(), name="attendance_timesheet"),
    path("calendar-export/", views.CalendarExportView.as_view(), name="attendance_calendar_export"),
    path("calendar-data/", views.CalendarDataView.as_view(), name="attendance_calendar_data"),
]
