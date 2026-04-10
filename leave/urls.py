from django.urls import path

from . import views

app_name = "leave"

urlpatterns = [
    # Employee views
    path("", views.LeaveListView.as_view(), name="leave_list"),
    path("request/", views.LeaveRequestView.as_view(), name="leave_request"),
    path("<int:pk>/", views.LeaveDetailView.as_view(), name="leave_detail"),
    
    # Admin views
    path("admin/", views.LeaveAdminListView.as_view(), name="leave_admin_list"),
    path("admin/dashboard/", views.LeaveDashboardView.as_view(), name="leave_admin_dashboard"),
    path("admin/<int:pk>/detail/", views.LeaveAdminDetailView.as_view(), name="leave_admin_detail"),
    path("admin/<int:pk>/approve/", views.LeaveApprovalView.as_view(), name="leave_approve"),
    path("admin/<int:pk>/reject/", views.LeaveRejectionView.as_view(), name="leave_reject"),
    # Simple action views for approve/reject
    path("admin/<int:pk>/approve-action/", views.LeaveApproveActionView.as_view(), name="leave_approve_action"),
    path("admin/<int:pk>/reject-action/", views.LeaveRejectActionView.as_view(), name="leave_reject_action"),
]
