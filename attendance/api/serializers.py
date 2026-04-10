from django.contrib.auth import get_user_model
from rest_framework import serializers

from attendance.models import Attendance

User = get_user_model()


class AttendanceSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Attendance
        fields = (
            "id",
            "user",
            "date",
            "check_in",
            "check_out",
            "total_hours",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "total_hours", "created_at", "updated_at")

    def validate(self, attrs):
        check_in = attrs.get("check_in")
        check_out = attrs.get("check_out")
        if self.instance is not None:
            if check_in is None:
                check_in = self.instance.check_in
            if check_out is None:
                check_out = self.instance.check_out
        if check_out and not check_in:
            raise serializers.ValidationError(
                {"check_out": "Check-out requires a check-in time."},
            )
        if self.instance is None and attrs.get("date"):
            user = attrs.get("user")
            if user is None and self.context.get("request"):
                user = self.context["request"].user
            if user and Attendance.objects.filter(
                user=user,
                date=attrs["date"],
            ).exists():
                raise serializers.ValidationError(
                    {"date": "An attendance record already exists for this user and date."},
                )
        return attrs
