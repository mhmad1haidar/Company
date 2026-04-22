from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormView

from accounts.models import User, Notification

from .forms import LeaveApprovalForm, LeaveFilterForm, LeaveRequestForm
from .models import Leave, LeaveType


class LeaveRequestView(LoginRequiredMixin, CreateView):
    """View for employees to create leave requests."""

    model = Leave
    form_class = LeaveRequestForm
    template_name = "leave/request_leave.html"
    success_url = reverse_lazy("leave:leave_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        leave = form.save(commit=False)
        leave.user = self.request.user
        leave.save()
        
        # Notify admins about new leave request
        admins = User.objects.filter(is_staff=True) | User.objects.filter(role__in=[User.Role.ADMIN, User.Role.MANAGER])
        for admin in admins.distinct():
            Notification.objects.create(
                recipient=admin,
                notification_type=Notification.NotificationType.LEAVE_REQUEST,
                title=f"New Leave Request - {self.request.user.get_full_name() or self.request.user.get_username()}",
                message=f"{self.request.user.get_full_name() or self.request.user.get_username()} has requested {leave.leave_type.name} from {leave.start_date} to {leave.end_date}.",
                link=f"/leave/admin/{leave.pk}/"
            )
        
        messages.success(
            self.request,
            "Your leave request has been submitted successfully.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Request Leave"
        return context


class LeaveListView(LoginRequiredMixin, ListView):
    """View for employees to see their own leave requests."""

    model = Leave
    template_name = "leave/leave_list.html"
    context_object_name = "leaves"
    paginate_by = 10

    def get_queryset(self):
        return (
            Leave.objects.filter(user=self.request.user)
            .select_related("leave_type", "approved_by")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "My Leave Requests"
        context["status_choices"] = Leave.Status.choices
        return context


class LeaveDetailView(LoginRequiredMixin, DetailView):
    """View for employees to see details of their leave request."""

    model = Leave
    template_name = "leave/leave_detail.html"
    context_object_name = "leave"

    def get_queryset(self):
        return (
            Leave.objects.filter(user=self.request.user)
            .select_related("leave_type", "approved_by")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Leave Request - {self.object.get_status_display()}"
        return context


class LeaveAdminDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View for admins to see details of any leave request including attachments."""

    model = Leave
    template_name = "leave/leave_admin_detail.html"
    context_object_name = "leave"

    def test_func(self):
        return self.request.user.is_staff or self.request.user.role in [
            User.Role.ADMIN,
            User.Role.MANAGER,
        ]

    def get_queryset(self):
        return Leave.objects.select_related("user", "leave_type", "approved_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        full_name = self.object.user.get_full_name()
        username = self.object.user.get_username()
        context["page_title"] = f"Leave Request - {full_name if full_name else username}"
        return context


class LeaveAdminListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for admins to see and manage all leave requests."""

    model = Leave
    template_name = "leave/admin_leave_list.html"
    context_object_name = "leaves"
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_staff or self.request.user.role in [
            User.Role.ADMIN,
            User.Role.MANAGER,
        ]

    def get_queryset(self):
        queryset = Leave.objects.select_related(
            "user", "leave_type", "approved_by"
        ).order_by("-created_at")

        # Apply filters
        self.filter_form = LeaveFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            cd = self.filter_form.cleaned_data
            
            if cd.get("status"):
                queryset = queryset.filter(status=cd["status"])
            
            if cd.get("leave_type"):
                queryset = queryset.filter(leave_type=cd["leave_type"])
            
            if cd.get("start_date_from"):
                queryset = queryset.filter(start_date__gte=cd["start_date_from"])
            
            if cd.get("start_date_to"):
                queryset = queryset.filter(start_date__lte=cd["start_date_to"])
            
            if cd.get("user"):
                queryset = queryset.filter(
                    Q(user__username__icontains=cd["user"])
                    | Q(user__first_name__icontains=cd["user"])
                    | Q(user__last_name__icontains=cd["user"])
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Leave Management"
        context["filter_form"] = self.filter_form
        context["status_choices"] = Leave.Status.choices
        context["pending_count"] = Leave.objects.filter(
            status=Leave.Status.PENDING
        ).count()
        
        # Add today's attendance data
        from attendance.models import Attendance
        from django.utils import timezone
        today = timezone.now().date()
        
        context["today_attendance"] = Attendance.objects.filter(
            date=today
        ).select_related('user').order_by('user__first_name', 'user__last_name')
        
        return context


class LeaveApprovalView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for admins to approve or reject leave requests."""

    model = Leave
    form_class = LeaveApprovalForm
    template_name = "leave/approve_leave.html"
    success_url = reverse_lazy("leave:leave_admin_list")

    def test_func(self):
        return self.request.user.is_staff or self.request.user.role in [
            User.Role.ADMIN,
            User.Role.MANAGER,
        ]

    def get_queryset(self):
        return Leave.objects.filter(status=Leave.Status.PENDING).select_related(
            "user", "leave_type"
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        leave = form.save()
        status = "approved" if leave.status == Leave.Status.APPROVED else "rejected"
        
        # Check if this is an AJAX request
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest' or self.request.content_type == 'application/x-www-form-urlencoded':
            # Return JSON response for AJAX
            from django.http import JsonResponse
            return JsonResponse({
                'status': 'success',
                'status_display': leave.get_status_display(),
                'status_color': leave.status_color,
                'approved_by': leave.approved_by.get_full_name() if leave.approved_by else leave.approved_by.get_username()
            })
        
        # Regular form submission
        messages.success(
            self.request,
            f"Leave request for {leave.user.get_username()} has been {status}.",
        )
        
        return super().form_valid(form)


class LeaveRejectionView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for admins to reject leave requests."""

    model = Leave
    form_class = LeaveApprovalForm
    template_name = "leave/approve_leave.html"
    success_url = reverse_lazy("leave:leave_admin_list")

    def test_func(self):
        return self.request.user.is_staff or self.request.user.role in [
            User.Role.ADMIN,
            User.Role.MANAGER,
        ]

    def get_queryset(self):
        return Leave.objects.filter(status=Leave.Status.PENDING).select_related(
            "user", "leave_type"
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Force status to rejected
        form.instance.status = Leave.Status.REJECTED
        leave = form.save()
        
        # Check if this is an AJAX request
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest' or self.request.content_type == 'application/x-www-form-urlencoded':
            # Return JSON response for AJAX
            from django.http import JsonResponse
            return JsonResponse({
                'status': 'success',
                'status_display': leave.get_status_display(),
                'status_color': leave.status_color,
                'approved_by': leave.approved_by.get_full_name() if leave.approved_by else leave.approved_by.get_username()
            })
        
        # Regular form submission
        messages.success(
            self.request,
            f"Leave request for {leave.user.get_username()} has been rejected.",
        )
        
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Review Leave Request - {self.object.user.get_username()}"
        return context


class LeaveDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Dashboard view for admins with leave statistics."""

    model = Leave
    template_name = "leave/dashboard.html"
    context_object_name = "recent_leaves"

    def test_func(self):
        return self.request.user.is_staff or self.request.user.role in [
            User.Role.ADMIN,
            User.Role.MANAGER,
        ]

    def get_queryset(self):
        return (
            Leave.objects.select_related("user", "leave_type")
            .order_by("-created_at")[:10]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics
        total_requests = Leave.objects.count()
        pending_requests = Leave.objects.filter(status=Leave.Status.PENDING).count()
        approved_requests = Leave.objects.filter(status=Leave.Status.APPROVED).count()
        rejected_requests = Leave.objects.filter(status=Leave.Status.REJECTED).count()
        
        # Current month stats
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        current_month_leaves = Leave.objects.filter(start_date__gte=current_month_start)
        
        # Attendance statistics
        from attendance.models import Attendance
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get today's attendance
        today_attendance = Attendance.objects.filter(date=today).select_related('user')
        
        # Currently checked in (checked in but not checked out) - count unique users
        currently_checked_in_user_ids = today_attendance.filter(
            check_in__isnull=False, 
            check_out__isnull=True
        ).values_list('user_id', flat=True).distinct()
        currently_checked_in_count = len(set(currently_checked_in_user_ids))
        
        # Checked out (have checked out) - count unique users
        checked_out_user_ids = today_attendance.filter(
            check_out__isnull=False
        ).values_list('user_id', flat=True).distinct()
        checked_out_count = len(set(checked_out_user_ids))
        
        # Get all active users
        all_active_users = User.objects.filter(is_active=True)
        
        # Users who have checked in at all today (regardless of check-out status)
        users_with_check_in_today = today_attendance.filter(
            check_in__isnull=False
        ).values_list('user_id', flat=True).distinct()
        
        # Calculate attendance stats
        total_users = all_active_users.count()
        users_with_check_in_count = len(set(users_with_check_in_today))
        not_checked_in_count = total_users - users_with_check_in_count
        
        # Get employee lists for the stat cards
        currently_checked_in_employees = today_attendance.filter(
            check_in__isnull=False, 
            check_out__isnull=True
        )
        checked_out_employees = today_attendance.filter(
            check_out__isnull=False
        )
        
        # Get users who haven't checked in today (no attendance record or no check-in)
        not_checked_in_employees = all_active_users.exclude(id__in=users_with_check_in_today)
        
        # Get recent attendance records
        recent_attendance = Attendance.objects.select_related('user').order_by('-date', '-check_in')[:10]
        
        context.update({
            "page_title": "Leave Dashboard",
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "approved_requests": approved_requests,
            "rejected_requests": rejected_requests,
            "current_month_leaves": current_month_leaves.count(),
            "leave_types": LeaveType.objects.all(),
            # Attendance data
            "total_users": total_users,
            "checked_in_count": currently_checked_in_count,
            "checked_out_count": checked_out_count,
            "not_checked_in_count": not_checked_in_count,
            "checked_in_employees": currently_checked_in_employees,
            "checked_out_employees": checked_out_employees,
            "not_checked_in_employees": not_checked_in_employees,
            "recent_attendance": recent_attendance,
        })
        
        return context


class LeaveApproveActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Simple view to approve a leave request via POST."""
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role in [
            User.Role.ADMIN,
            User.Role.MANAGER,
        ]
    
    def post(self, request, pk):
        leave = get_object_or_404(Leave, pk=pk, status=Leave.Status.PENDING)
        leave.status = Leave.Status.APPROVED
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()
        
        # Notify the user about approval
        Notification.objects.create(
            recipient=leave.user,
            notification_type=Notification.NotificationType.LEAVE_APPROVED,
            title="Leave Request Approved",
            message=f"Your {leave.leave_type.name} leave from {leave.start_date} to {leave.end_date} has been approved.",
            link="/leave/"
        )
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'status_display': leave.get_status_display(),
                'status_color': leave.status_color,
                'approved_by': leave.approved_by.get_full_name() if leave.approved_by.get_full_name() else leave.approved_by.get_username()
            })
        
        # Regular form submission - redirect to admin list
        full_name = leave.user.get_full_name()
        username = leave.user.get_username()
        messages.success(request, f"Leave request for {full_name if full_name else username} has been approved.")
        return redirect('leave:leave_admin_list')


class LeaveRejectActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Simple view to reject a leave request via POST."""
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role in [
            User.Role.ADMIN,
            User.Role.MANAGER,
        ]
    
    def post(self, request, pk):
        leave = get_object_or_404(Leave, pk=pk, status=Leave.Status.PENDING)
        leave.status = Leave.Status.REJECTED
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()
        
        # Notify the user about rejection
        Notification.objects.create(
            recipient=leave.user,
            notification_type=Notification.NotificationType.LEAVE_REJECTED,
            title="Leave Request Rejected",
            message=f"Your {leave.leave_type.name} leave from {leave.start_date} to {leave.end_date} has been rejected.",
            link="/leave/"
        )
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'status_display': leave.get_status_display(),
                'status_color': leave.status_color,
                'approved_by': leave.approved_by.get_full_name() if leave.approved_by.get_full_name() else leave.approved_by.get_username()
            })
        
        # Regular form submission - redirect to admin list
        full_name = leave.user.get_full_name()
        username = leave.user.get_username()
        messages.success(request, f"Leave request for {full_name if full_name else username} has been rejected.")
        return redirect('leave:leave_admin_list')
