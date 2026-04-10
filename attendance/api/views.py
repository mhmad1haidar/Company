from django.db import IntegrityError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from attendance.exceptions import DuplicateAttendanceError
from attendance.models import Attendance
from attendance.services import check_in as record_check_in
from attendance.services import check_out as record_check_out

from .serializers import AttendanceSerializer


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Attendance.objects.select_related("user").all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs.order_by("-date", "-check_in")

    def perform_create(self, serializer):
        user = serializer.validated_data.get("user") or self.request.user
        if not self.request.user.is_staff and user != self.request.user:
            raise permissions.PermissionDenied("You may only create your own records.")
        try:
            serializer.save(user=user)
        except IntegrityError as exc:
            raise DuplicateAttendanceError() from exc

    def perform_update(self, serializer):
        if not self.request.user.is_staff and serializer.instance.user != self.request.user:
            raise permissions.PermissionDenied("You may only update your own records.")
        try:
            serializer.save()
        except IntegrityError as exc:
            raise DuplicateAttendanceError() from exc

    @action(detail=False, methods=["post"])
    def check_in(self, request):
        record = record_check_in(request.user)
        return Response(
            AttendanceSerializer(record).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def check_out(self, request):
        record = record_check_out(request.user)
        return Response(
            AttendanceSerializer(record).data,
            status=status.HTTP_200_OK,
        )
