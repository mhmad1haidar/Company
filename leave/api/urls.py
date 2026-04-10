from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LeaveTypeViewSet, LeaveViewSet

router = DefaultRouter()
router.register("types", LeaveTypeViewSet, basename="leave-type")
router.register("requests", LeaveViewSet, basename="leave")

urlpatterns = [
    path("", include(router.urls)),
]
