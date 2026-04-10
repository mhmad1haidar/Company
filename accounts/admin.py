from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """HR-focused directory of people (accounts)."""

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Profile",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "role",
                    "employee_id",
                    "department",
                    "job_title",
                ),
            },
        ),
        (
            "Access",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "fields": ("last_login", "date_joined"),
                "description": (
                    "Account creation time is stored in date_joined (set automatically)."
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "role",
                    "department",
                    "employee_id",
                    "job_title",
                ),
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "get_full_name_display",
        "employee_id",
        "role",
        "department",
        "job_title",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_display_links = ("username",)
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "role",
        "department",
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "employee_id",
        "job_title",
        "department",
    )
    ordering = ("username",)
    date_hierarchy = "date_joined"
    list_per_page = 50
    show_full_result_count = False
    save_on_top = True

    empty_value_display = "—"

    @admin.display(description="Full name", ordering="last_name")
    def get_full_name_display(self, obj: User) -> str:
        full = obj.get_full_name().strip()
        return full or "—"
