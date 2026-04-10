"""
Reusable admin list filters for models linked to :class:`accounts.User`.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


class UserDepartmentFilter(admin.SimpleListFilter):
    """Filter rows by the related user's department (distinct values from User)."""

    title = "Department"
    parameter_name = "user_department"

    def lookups(self, request, model_admin):
        depts = (
            User.objects.exclude(department__exact="")
            .values_list("department", flat=True)
            .distinct()
            .order_by("department")
        )
        return [(d, d) for d in depts]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__department=self.value())
        return queryset
