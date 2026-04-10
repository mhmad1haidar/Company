from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from leave.models import Leave, LeaveType
from leave.services import LeaveService

from .serializers import LeaveSerializer, LeaveTypeSerializer


class LeaveTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class LeaveViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Leave.objects.select_related("user", "approved_by", "leave_type").all()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs.order_by("-created_at")

    def perform_update(self, serializer):
        if not self.request.user.is_staff and serializer.instance.user != self.request.user:
            raise permissions.PermissionDenied("You may only edit your own requests.")
        if serializer.instance.status != Leave.Status.PENDING:
            raise permissions.PermissionDenied("Only pending requests can be edited.")
        serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        if not request.user.is_staff:
            return Response(
                {"detail": "Staff only."},
                status=status.HTTP_403_FORBIDDEN,
            )
        leave = self.get_object()
        leave = LeaveService.approve(leave, request.user)
        return Response(LeaveSerializer(leave).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        if not request.user.is_staff:
            return Response(
                {"detail": "Staff only."},
                status=status.HTTP_403_FORBIDDEN,
            )
        leave = self.get_object()
        leave = LeaveService.reject(leave, request.user)
        return Response(LeaveSerializer(leave).data, status=status.HTTP_200_OK)
