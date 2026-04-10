from django.contrib import admin
from django.contrib.admin import DateFieldListFilter

from company.admin_filters import UserDepartmentFilter

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Daily attendance records for HR review."""

    list_display = (
        "user",
        "user_department",
        "date",
        "status",
        "check_in",
        "check_out",
        "display_total_hours",
    )
    list_display_links = ("user", "date")
    list_filter = (
        UserDepartmentFilter,
        "status",
        ("date", DateFieldListFilter),
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__employee_id",
        "user__department",
    )
    autocomplete_fields = ("user",)
    date_hierarchy = "date"
    ordering = ("-date", "-check_in")
    list_per_page = 50
    show_full_result_count = False
    save_on_top = True
    empty_value_display = "—"

    fieldsets = (
        (
            "Employee & day",
            {"fields": ("user", "date", "status")},
        ),
        (
            "Times",
            {
                "fields": ("check_in", "check_out", "total_hours"),
                "description": "Total hours are calculated automatically when both times are set.",
            },
        ),
        (
            "Audit",
            {"fields": ("created_at", "updated_at")},
        ),
    )
    readonly_fields = ("total_hours", "created_at", "updated_at")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user")
        )

    @admin.display(description="Department", ordering="user__department")
    def user_department(self, obj: Attendance) -> str:
        return obj.user.department or "—"

    @admin.display(description="Hours", ordering="total_hours")
    def display_total_hours(self, obj: Attendance) -> str:
        if obj.total_hours is None:
            return "—"
        return f"{obj.total_hours} h"
