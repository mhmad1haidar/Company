from django.contrib.auth import get_user_model
from rest_framework import mixins, permissions, viewsets

from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Staff can list all users; non-staff users only see and update themselves.
    User creation/removal is intended for admin or future dedicated endpoints.
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all().order_by("username")
        return User.objects.filter(pk=user.pk)
