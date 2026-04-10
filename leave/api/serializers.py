from django.contrib.auth import get_user_model
from rest_framework import serializers

from leave.models import Leave, LeaveType
from leave.services import LeaveService

User = get_user_model()


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ("id", "code", "name", "description")


class LeaveSerializer(serializers.ModelSerializer):
    leave_type = serializers.PrimaryKeyRelatedField(queryset=LeaveType.objects.all())
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Leave
        fields = (
            "id",
            "user",
            "leave_type",
            "start_date",
            "end_date",
            "status",
            "reason",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data):
        request = self.context["request"]
        user = validated_data.pop("user", None) or request.user
        if not request.user.is_staff and user != request.user:
            raise serializers.ValidationError(
                {"user": "You may only submit leave for yourself."},
            )
        return LeaveService.submit(
            user=user,
            leave_type=validated_data["leave_type"],
            start_date=validated_data["start_date"],
            end_date=validated_data["end_date"],
            reason=validated_data.get("reason", ""),
        )

    def update(self, instance, validated_data):
        validated_data.pop("user", None)
        validated_data.pop("leave_type", None)
        return super().update(instance, validated_data)
