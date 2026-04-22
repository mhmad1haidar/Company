from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, Count, Sum, Avg, F
from django.db.models.functions import TruncDate, TruncMonth
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import FormView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from attendance.models import Attendance

from .models import Notification, Announcement, Message, Widget, UserWidget, QuickAction, UserQuickAction

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
        context["inactive_employees"] = User.objects.filter(is_active=False).count()
        
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
        
        # Load user's enabled widgets
        user_widgets = UserWidget.objects.filter(
            user=self.request.user,
            is_enabled=True
        ).select_related('widget').order_by('order')
        context['user_widgets'] = user_widgets
        
        # Load user's enabled quick actions
        user_quick_actions = UserQuickAction.objects.filter(
            user=self.request.user,
            is_enabled=True
        ).select_related('quick_action').order_by('order')
        context['user_quick_actions'] = user_quick_actions
        
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
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M')
            })

        return JsonResponse({'notifications': data})


@require_http_methods(["POST"])
@login_required
def toggle_dark_mode(request):
    """Toggle dark mode preference for user"""
    try:
        data = json.loads(request.body)
        dark_mode = data.get('dark_mode', False)

        request.user.dark_mode = dark_mode
        request.user.save()

        return JsonResponse({'success': True, 'dark_mode': dark_mode})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


class AnnouncementListView(LoginRequiredMixin, ListView):
    """List all announcements for the current user"""
    model = Announcement
    template_name = 'accounts/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 10

    def get_queryset(self):
        queryset = Announcement.objects.filter(
            is_active=True,
            start_date__lte=timezone.now()
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
        )

        # Filter by target audience
        user = self.request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            pass  # Admins see all
        elif user.is_staff or user.role == User.Role.MANAGER:
            queryset = queryset.filter(target_audience__in=['all', 'staff', 'managers'])
        else:
            queryset = queryset.filter(target_audience='all')

        return queryset.select_related('author')


class AnnouncementDetailView(LoginRequiredMixin, DetailView):
    """View announcement details"""
    model = Announcement
    template_name = 'accounts/announcement_detail.html'
    context_object_name = 'announcement'


class AnnouncementCreateView(LoginRequiredMixin, CreateView):
    """Create a new announcement (admin/staff only)"""
    model = Announcement
    template_name = 'accounts/announcement_form.html'
    fields = ['title', 'content', 'priority', 'target_audience', 'is_active', 'start_date', 'end_date']
    success_url = reverse_lazy('accounts:announcement-list')

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('accounts:announcement-list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Announcement created successfully')
        return super().form_valid(form)


class AnnouncementUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing announcement (author or admin only)"""
    model = Announcement
    template_name = 'accounts/announcement_form.html'
    fields = ['title', 'content', 'priority', 'target_audience', 'is_active', 'start_date', 'end_date']
    success_url = reverse_lazy('accounts:announcement-list')

    def dispatch(self, request, *args, **kwargs):
        announcement = self.get_object()
        if request.user != announcement.author and not request.user.is_superuser:
            return redirect('accounts:announcement-list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Announcement updated successfully')
        return super().form_valid(form)


class AnnouncementDeleteView(LoginRequiredMixin, View):
    """Delete an announcement (author or admin only)"""

    def post(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk)
        if request.user == announcement.author or request.user.is_superuser:
            announcement.delete()
            messages.success(request, 'Announcement deleted successfully')
        else:
            messages.error(request, 'You do not have permission to delete this announcement')
        return redirect('accounts:announcement-list')


class AnnouncementDashboardView(LoginRequiredMixin, View):
    """Get active announcements for dashboard widget"""

    def get(self, request):
        queryset = Announcement.objects.filter(
            is_active=True,
            start_date__lte=timezone.now()
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
        )

        # Filter by target audience
        user = request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            pass
        elif user.is_staff or user.role == User.Role.MANAGER:
            queryset = queryset.filter(target_audience__in=['all', 'staff', 'managers'])
        else:
            queryset = queryset.filter(target_audience='all')

        announcements = queryset.order_by('-priority', '-created_at')[:5]

        data = []
        for announcement in announcements:
            data.append({
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content[:200] + '...' if len(announcement.content) > 200 else announcement.content,
                'priority': announcement.priority,
                'priority_display': announcement.get_priority_display(),
                'author': announcement.author.get_full_name(),
                'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M'),
            })

        return JsonResponse({'announcements': data})


class MessageInboxView(LoginRequiredMixin, ListView):
    """View received messages (inbox)"""
    model = Message
    template_name = 'accounts/message_inbox.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(
            recipient=self.request.user
        ).select_related('sender').order_by('-created_at')


class MessageSentView(LoginRequiredMixin, ListView):
    """View sent messages"""
    model = Message
    template_name = 'accounts/message_sent.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(
            sender=self.request.user
        ).select_related('recipient').order_by('-created_at')


class MessageDetailView(LoginRequiredMixin, DetailView):
    """View message details"""
    model = Message
    template_name = 'accounts/message_detail.html'
    context_object_name = 'message'

    def get_queryset(self):
        return Message.objects.filter(
            models.Q(sender=self.request.user) | models.Q(recipient=self.request.user)
        ).select_related('sender', 'recipient')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        message = self.object

        # Mark as read if the current user is the recipient
        if message.recipient == self.request.user and not message.is_read:
            message.mark_as_read()

        # Get replies
        context['replies'] = message.replies.all().select_related('sender', 'recipient')

        return context


class MessageComposeView(LoginRequiredMixin, CreateView):
    """Compose a new message"""
    model = Message
    template_name = 'accounts/message_form.html'
    fields = ['recipient', 'subject', 'body']
    success_url = reverse_lazy('accounts:message-inbox')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['recipient'].queryset = User.objects.filter(is_active=True).exclude(pk=self.request.user.pk)
        return form

    def form_valid(self, form):
        form.instance.sender = self.request.user
        messages.success(self.request, 'Message sent successfully')
        return super().form_valid(form)


class MessageReplyView(LoginRequiredMixin, CreateView):
    """Reply to a message"""
    model = Message
    template_name = 'accounts/message_form.html'
    fields = ['recipient', 'subject', 'body']

    def dispatch(self, request, *args, **kwargs):
        parent_message = get_object_or_404(Message, pk=kwargs['pk'])
        if request.user not in [parent_message.sender, parent_message.recipient]:
            return redirect('accounts:message-inbox')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        parent_message = get_object_or_404(Message, pk=self.kwargs['pk'])
        return {
            'recipient': parent_message.sender if parent_message.recipient == self.request.user else parent_message.recipient,
            'subject': f'Re: {parent_message.subject}',
        }

    def form_valid(self, form):
        form.instance.sender = self.request.user
        form.instance.parent_message_id = self.kwargs['pk']
        messages.success(self.request, 'Reply sent successfully')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('accounts:message-detail', kwargs={'pk': self.kwargs['pk']})
