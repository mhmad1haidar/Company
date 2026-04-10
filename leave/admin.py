from django.contrib import admin
from django.contrib.admin import DateFieldListFilter

from company.admin_filters import UserDepartmentFilter

from .models import Leave, LeaveType


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    """Reference list of leave categories."""

    list_display = ("code", "name", "description_short")
    search_fields = ("code", "name", "description")
    ordering = ("name",)
    list_per_page = 50

    @admin.display(description="Description")
    def description_short(self, obj: LeaveType) -> str:
        if not obj.description:
            return "—"
        return (obj.description[:80] + "…") if len(obj.description) > 80 else obj.description


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    """Leave requests for approval and reporting."""

    list_display = (
        "user",
        "user_department",
        "leave_type",
        "start_date",
        "end_date",
        "duration_days",
        "status",
        "approved_by",
        "approved_at",
        "created_at",
    )
    list_display_links = ("user", "start_date")
    list_filter = (
        UserDepartmentFilter,
        "status",
        "leave_type",
        ("start_date", DateFieldListFilter),
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__employee_id",
        "user__department",
        "reason",
    )
    autocomplete_fields = ("user", "approved_by", "leave_type")
    date_hierarchy = "start_date"
    ordering = ("-created_at",)
    list_per_page = 50
    show_full_result_count = False
    save_on_top = True
    empty_value_display = "—"

    fieldsets = (
        (
            "Employee & type",
            {"fields": ("user", "leave_type")},
        ),
        (
            "Dates",
            {"fields": ("start_date", "end_date")},
        ),
        (
            "Request",
            {"fields": ("status", "reason")},
        ),
        (
            "Approval",
            {"fields": ("approved_by", "approved_at")},
        ),
        (
            "Audit",
            {"fields": ("created_at", "updated_at")},
        ),
    )
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "leave_type", "approved_by")
        )

    @admin.display(description="Department", ordering="user__department")
    def user_department(self, obj: Leave) -> str:
        return obj.user.department or "—"

    @admin.display(description="Days")
    def duration_days(self, obj: Leave) -> str:
        if not obj.start_date or not obj.end_date:
            return "—"
        days = (obj.end_date - obj.start_date).days + 1
        return str(days)
