from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F
from django.db.models.functions import TruncDate, TruncMonth
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import FormView

from attendance.models import Attendance

from .models import Notification

User = get_user_model()

from .forms import StyledAuthenticationForm


class AppLoginView(LoginView):
    """Session login with enhanced security and user feedback."""

    template_name = "accounts/login.html"
    form_class = StyledAuthenticationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("accounts:dashboard")

    def form_invalid(self, form):
        """Add error message for invalid credentials."""
        messages.error(
            self.request,
            "Invalid username or password. Please try again.",
            extra_tags='danger'
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        """Add success message for successful login."""
        # Removed welcome back message
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to next parameter if provided, otherwise default."""
        next_url = self.request.GET.get('next')
        if next_url and next_url.strip():
            return next_url
        return self.success_url


class AppLogoutView(LogoutView):
    """POST-only logout with CSRF protection and user feedback."""

    next_page = reverse_lazy("accounts:login")
    http_method_names = ["post", "options"]

    def dispatch(self, request, *args, **kwargs):
        """Store username for success message before logout."""
        if request.user.is_authenticated:
            self.username = request.user.get_username()
        else:
            self.username = None
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Add success message after logout."""
        response = super().post(request, *args, **kwargs)
        if self.username:
            messages.success(
                request,
                f"You have been successfully logged out, {self.username}."
            )
        return response


class DashboardView(LoginRequiredMixin, TemplateView):
    """Home for authenticated users; shows today's attendance summary."""

    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        context["today"] = today
        
        # Real data from existing apps
        context["total_employees"] = User.objects.filter(is_active=True).count()
        
        # Fleet statistics (from fleet app)
        try:
            from fleet.models import Car
            total_cars = Car.objects.count()
            active_cars = Car.objects.filter(status='available').count()
            context["fleet_active"] = active_cars
            context["fleet_total"] = total_cars
        except ImportError:
            context["fleet_active"] = 0
            context["fleet_total"] = 0
        
        # Interventions statistics (from interventions app)
        try:
            from interventions.models import Intervention
            total_interventions = Intervention.objects.count()
            # Count active interventions (not completed or cancelled)
            active_interventions = Intervention.objects.filter(
                stato_avanzamento_nigit__in=['DA_INIZIARE', 'IN_CORSO', 'SOSPESO']
            ).count()
            context["active_interventions"] = active_interventions
            context["total_interventions"] = total_interventions
        except ImportError:
            context["active_interventions"] = 0
            context["total_interventions"] = 0
        
        # Leave statistics (from leave app) - Only keep pending count
        try:
            from leave.models import LeaveRequest
            context["pending_leave_requests"] = LeaveRequest.objects.filter(status='pending').count()
        except ImportError:
            context["pending_leave_requests"] = 0
        
        # Work assignments statistics (from assignments app)
        try:
            from assignments.models import WorkAssignment
            from django.db.models import Count, Q
            
            total_assignments = WorkAssignment.objects.count()
            # Count active assignments (not completed or cancelled)
            active_assignments = WorkAssignment.objects.filter(
                status__in=['pending', 'assigned', 'in_progress']
            ).count()
            # Individual status counts for dashboard
            pending_assignments = WorkAssignment.objects.filter(status='pending').count()
            assigned_assignments = WorkAssignment.objects.filter(status='assigned').count()
            in_progress_assignments = WorkAssignment.objects.filter(status='in_progress').count()
            # Count assignments for current user
            user_assignments = WorkAssignment.objects.filter(
                assigned_to=self.request.user
            ).count()
            # Get recent assignments for current user (last 10)
            recent_assignments = WorkAssignment.objects.filter(
                assigned_to=self.request.user
            ).select_related(
                'intervention'
            ).prefetch_related(
                'assigned_to'
            ).order_by('-assigned_date')[:10]
            
            # Get current user's assignment statistics
            user_pending = WorkAssignment.objects.filter(
                assigned_to=self.request.user, status='pending'
            ).count()
            user_in_progress = WorkAssignment.objects.filter(
                assigned_to=self.request.user, status='in_progress'
            ).count()
            user_completed_worked = WorkAssignment.objects.filter(
                assigned_to=self.request.user, status='completed'
            ).count()
            user_completed_not_worked = WorkAssignment.objects.filter(
                assigned_to=self.request.user, status='not_worked'
            ).count()
            user_assigned = WorkAssignment.objects.filter(
                assigned_to=self.request.user, status='assigned'
            ).count()
            
            # Get recent assignments with work performed info
            recent_assignments = WorkAssignment.objects.filter(
                assigned_to=self.request.user
            ).select_related(
                'intervention'
            ).prefetch_related(
                'assigned_to'
            ).order_by('-assigned_date')[:10]
            
            # Get overall completed statistics for admin dashboard
            completed_worked_total = WorkAssignment.objects.filter(status='completed').count()
            completed_not_worked_total = WorkAssignment.objects.filter(status='not_worked').count()
            
            # For regular users, don't show other users' assignments
            if self.request.user.is_superuser or self.request.user.has_perm('assignments.view_all_assignments'):
                # Admin/Manager can see all users
                users_with_assignments = User.objects.filter(
                    work_assignments__isnull=False
                ).distinct().annotate(
                    assignment_count=Count('work_assignments'),
                    pending_count=Count('work_assignments', filter=Q(work_assignments__status='pending')),
                    in_progress_count=Count('work_assignments', filter=Q(work_assignments__status='in_progress')),
                    completed_worked_count=Count('work_assignments', filter=Q(work_assignments__status='completed')),
                    completed_not_worked_count=Count('work_assignments', filter=Q(work_assignments__status='not_worked'))
                ).order_by('first_name', 'last_name')
                
                # Get recent assignments for each user
                user_assignments_dict = {}
                for user in users_with_assignments:
                    recent_user_assignments = WorkAssignment.objects.filter(
                        assigned_to=user
                    ).select_related(
                        'intervention'
                    ).prefetch_related(
                        'assigned_to'
                    ).order_by('-assigned_date')[:5]
                    user_assignments_dict[user.id] = recent_user_assignments
                
                context["users_with_assignments"] = users_with_assignments
                context["user_assignments_dict"] = user_assignments_dict
                context["show_all_users"] = True
            else:
                # Regular user only sees their own assignments
                context["show_all_users"] = False
            
            completed_assignments = WorkAssignment.objects.filter(status__in=['completed', 'not_worked']).count()
            context["total_assignments"] = total_assignments
            context["active_assignments"] = active_assignments
            context["pending_assignments"] = pending_assignments
            context["assigned_assignments"] = assigned_assignments
            context["in_progress_assignments"] = in_progress_assignments
            context["user_assignments"] = user_assignments
            context["recent_assignments"] = recent_assignments
            context["completed_assignments"] = completed_assignments
            context["completed_worked_total"] = completed_worked_total
            context["completed_not_worked_total"] = completed_not_worked_total
            context["user_pending"] = user_pending
            context["user_in_progress"] = user_in_progress
            context["user_completed_worked"] = user_completed_worked
            context["user_completed_not_worked"] = user_completed_not_worked
            context["user_assigned"] = user_assigned
        except ImportError:
            context["total_assignments"] = 0
            context["active_assignments"] = 0
            context["pending_assignments"] = 0
            context["assigned_assignments"] = 0
            context["in_progress_assignments"] = 0
            context["user_assignments"] = 0
            context["recent_assignments"] = []
            context["completed_assignments"] = 0
            context["completed_worked_total"] = 0
            context["completed_not_worked_total"] = 0
            context["user_pending"] = 0
            context["user_in_progress"] = 0
            context["user_completed_worked"] = 0
            context["user_completed_not_worked"] = 0
            context["user_assigned"] = 0
            context["show_all_users"] = False
        
        return context


class NotificationListView(LoginRequiredMixin, ListView):
    """View for user's notifications"""
    model = Notification
    template_name = 'accounts/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related('recipient').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Notifications'
        context['unread_count'] = Notification.objects.filter(
            recipient=self.request.user, is_read=False
        ).count()
        return context


class NotificationDetailView(LoginRequiredMixin, View):
    """Mark notification as read and redirect"""
    
    def get(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.is_read = True
        notification.save()
        if notification.link:
            return redirect(notification.link)
        return redirect('accounts:notifications')


class MarkAllAsReadView(LoginRequiredMixin, View):
    """Mark all notifications as read"""
    
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success', 'message': 'All notifications marked as read'})


class NotificationCountView(LoginRequiredMixin, View):
    """Get unread notification count"""
    
    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'count': count})


class RecentNotificationsView(LoginRequiredMixin, View):
    """Get recent notifications for dropdown"""
    
    def get(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:5]
        
        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%b %d, %H:%M'),
                'link': notification.link
            })
        
        return JsonResponse({'notifications': data})
