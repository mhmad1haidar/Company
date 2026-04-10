from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "employee_id",
            "department",
            "job_title",
            "is_staff",
            "date_joined",
        )
        read_only_fields = ("id", "username", "is_staff", "date_joined")

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff:
            fields["role"].read_only = True
        return fields
