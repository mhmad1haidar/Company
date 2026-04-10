from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse

from .models import WorkAssignment
from .forms import WorkAssignmentForm, WorkAssignmentStatusForm
from interventions.models import Intervention
from accounts.models import Notification


class WorkAssignmentListView(LoginRequiredMixin, ListView):
    """List view for work assignments"""
    model = WorkAssignment
    template_name = 'assignments/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('intervention', 'vehicle').prefetch_related('assigned_to', 'status_history')
        queryset = queryset.order_by('-created_at')
        
        # Filter by user if not admin/manager
        if not self.request.user.has_perm('assignments.view_all_assignments'):
            queryset = queryset.filter(assigned_to=self.request.user)
        
        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(codice_nigit__icontains=search) |
                Q(intervention__cliente__icontains=search) |
                Q(intervention__nome__icontains=search) |
                Q(assigned_to__first_name__icontains=search) |
                Q(assigned_to__last_name__icontains=search) |
                Q(assignment_note__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Work Assignments'
        context['status_choices'] = WorkAssignment.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Group assignments by intervention
        from collections import defaultdict
        interventions_dict = defaultdict(list)
        for assignment in context['assignments']:
            if assignment.intervention:
                interventions_dict[assignment.intervention].append(assignment)
        
        # Create intervention summary with work status
        intervention_summaries = []
        for intervention, assignments in interventions_dict.items():
            total_assignments = len(assignments)
            completed_worked = sum(1 for a in assignments if a.status == 'completed' and a.work_performed)
            completed_not_worked = sum(1 for a in assignments if a.status == 'completed' and not a.work_performed)
            in_progress = sum(1 for a in assignments if a.status == 'in_progress')
            pending = sum(1 for a in assignments if a.status == 'pending')
            assigned = sum(1 for a in assignments if a.status == 'assigned')
            cancelled = sum(1 for a in assignments if a.status == 'cancelled')
            
            # Get all unique workers
            all_workers = set()
            for a in assignments:
                all_workers.update(a.assigned_to.all())
            
            intervention_summaries.append({
                'intervention': intervention,
                'assignments': assignments,
                'total_assignments': total_assignments,
                'completed_worked': completed_worked,
                'completed_not_worked': completed_not_worked,
                'in_progress': in_progress,
                'pending': pending,
                'assigned': assigned,
                'cancelled': cancelled,
                'workers': list(all_workers),
                'total_workers': len(all_workers),
                'latest_assignment': max(assignments, key=lambda a: a.created_at)
            })
        
        # Sort by latest assignment date
        intervention_summaries.sort(key=lambda x: x['latest_assignment'].created_at, reverse=True)
        
        context['intervention_summaries'] = intervention_summaries
        
        # Add statistics
        if self.request.user.has_perm('assignments.view_all_assignments'):
            context['stats'] = {
                'total': WorkAssignment.objects.count(),
                'pending': WorkAssignment.objects.filter(status='pending').count(),
                'assigned': WorkAssignment.objects.filter(status='assigned').count(),
                'in_progress': WorkAssignment.objects.filter(status='in_progress').count(),
                'completed': WorkAssignment.objects.filter(status='completed').count(),
            }
        else:
            user_assignments = WorkAssignment.objects.filter(assigned_to=self.request.user)
            context['stats'] = {
                'total': user_assignments.count(),
                'pending': user_assignments.filter(status='pending').count(),
                'assigned': user_assignments.filter(status='assigned').count(),
                'in_progress': user_assignments.filter(status='in_progress').count(),
                'completed': user_assignments.filter(status='completed').count(),
            }
        
        return context


class WorkAssignmentDetailView(LoginRequiredMixin, DetailView):
    """Detail view for work assignment"""
    model = WorkAssignment
    template_name = 'assignments/assignment_detail.html'
    context_object_name = 'assignment'
    
    def get_queryset(self):
        return WorkAssignment.objects.select_related(
            'intervention', 'vehicle', 'created_by'
        ).prefetch_related(
            'assigned_to'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Assignment: {self.object.codice_nigit}'
        context['status_form'] = WorkAssignmentStatusForm(instance=self.object)
        
        # Check if user can update status
        can_update_status = (
            self.request.user in self.object.assigned_to.all() or 
            self.request.user.has_perm('assignments.change_assignment')
        )
        context['can_update_status'] = can_update_status
        
        return context


class WorkAssignmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for work assignments"""
    model = WorkAssignment
    form_class = WorkAssignmentForm
    template_name = 'assignments/assignment_form.html'
    success_url = reverse_lazy('assignments:assignment-list')
    permission_required = 'assignments.add_assignment'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        assignment = form.save()
        
        # Notify assigned employees
        for employee in assignment.assigned_to.all():
            Notification.objects.create(
                recipient=employee,
                notification_type=Notification.NotificationType.ASSIGNMENT_NEW,
                title="New Work Assignment",
                message=f"You have been assigned to work on intervention {assignment.intervention.codice_nigit if assignment.intervention else 'N/A'} - {assignment.intervention.nome if assignment.intervention else 'N/A'}",
                link=f"/assignments/assignment/{assignment.pk}/"
            )
        
        messages.success(self.request, f'Work assignment for {assignment.codice_nigit} created successfully!')
        return redirect('assignments:assignment-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Work Assignment'
        context['action'] = 'create'
        return context


class WorkAssignmentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for work assignments"""
    model = WorkAssignment
    form_class = WorkAssignmentForm
    template_name = 'assignments/assignment_form.html'
    success_url = reverse_lazy('assignments:assignment-list')
    permission_required = 'assignments.change_assignment'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        assignment = form.save()
        
        # Notify assigned employees about status change
        old_status = self.object.status if self.object else None
        new_status = assignment.status
        
        if old_status != new_status:
            for employee in assignment.assigned_to.all():
                Notification.objects.create(
                    recipient=employee,
                    notification_type=Notification.NotificationType.ASSIGNMENT_STATUS_CHANGE,
                    title="Assignment Status Updated",
                    message=f"Assignment for intervention {assignment.intervention.codice_nigit if assignment.intervention else 'N/A'} status changed from {old_status} to {new_status}.",
                    link=f"/assignments/assignment/{assignment.pk}/"
                )
        
        messages.success(self.request, f'Work assignment for {assignment.codice_nigit} updated successfully!')
        return redirect('assignments:assignment-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Work Assignment'
        context['action'] = 'update'
        return context


@login_required
def update_work_status(request, pk):
    """Update assignment work status via AJAX"""
    assignment = get_object_or_404(WorkAssignment, pk=pk)
    
    # Check if user can update this assignment
    if request.user not in assignment.assigned_to.all() and not request.user.has_perm('assignments.change_assignment'):
        return JsonResponse({'error': 'Permission denied - you must be assigned to this assignment or have admin permissions'}, status=403)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        work_performed = request.POST.get('work_performed', 'true').lower() == 'true'
        completion_note = request.POST.get('completion_note', '')
        
        if new_status in dict(WorkAssignment.STATUS_CHOICES):
            old_status = assignment.status
            assignment.status = new_status
            
            # If marking as completed, set completion details
            if new_status == 'completed':
                assignment.completed_by = request.user
                assignment.completed_date = timezone.now()
                assignment.work_performed = work_performed
                if completion_note:
                    assignment.completion_note = completion_note
            elif old_status == 'completed':
                # If changing from completed, clear completion details
                assignment.completed_by = None
                assignment.completed_date = None
                assignment.completion_note = ''
            
            assignment.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Status updated to {assignment.get_status_display()}',
                'new_status': assignment.status,
                'new_status_display': assignment.get_status_display(),
                'work_performed': assignment.work_performed if assignment.status == 'completed' else None
            })
        else:
            return JsonResponse({'error': 'Invalid status'}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def complete_assignment(request, pk):
    """Complete assignment with note"""
    assignment = get_object_or_404(WorkAssignment, pk=pk)
    
    # Check if user can complete this assignment
    if request.user not in assignment.assigned_to.all() and not request.user.has_perm('assignments.change_assignment'):
        return JsonResponse({'error': 'Permission denied - you must be assigned to this assignment or have admin permissions'}, status=403)
    
    if assignment.status == 'completed':
        return JsonResponse({'error': 'Assignment already completed'}, status=400)
    
    if request.method == 'POST':
        completion_note = request.POST.get('completion_note', '')
        work_performed = request.POST.get('work_performed', 'true').lower() == 'true'
        
        try:
            assignment.mark_complete(request.user, completion_note, work_performed)
            return JsonResponse({
                'success': True,
                'message': 'Assignment marked as completed',
                'completed_date': assignment.completed_date.strftime('%d/%m/%Y %H:%M'),
                'completed_by': assignment.completed_by.get_full_name() or assignment.completed_by.username,
                'work_performed': assignment.work_performed
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def update_assignment_status(request, pk):
    """Update assignment status via AJAX"""
    assignment = get_object_or_404(WorkAssignment, pk=pk)
    
    # Check permissions - allow admin/staff/manager to change any assignment status
    can_update = (
        request.user.is_superuser or 
        request.user.is_staff or 
        request.user.role in 'admin,manager' or
        assignment.assigned_to == request.user or 
        request.user.has_perm('assignments.change_assignment')
    )
    
    if not can_update:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        import json
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                new_status = data.get('status')
            else:
                new_status = request.POST.get('status')
            
            if new_status in dict(WorkAssignment.STATUS_CHOICES):
                old_status = assignment.status
                assignment.status = new_status
                assignment.save()
                
                # Record status history
                from .models import AssignmentStatusHistory
                AssignmentStatusHistory.objects.create(
                    assignment=assignment,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=request.user
                )
                
                return JsonResponse({
                    'success': True,
                    'new_status': assignment.get_status_display(),
                    'old_status': old_status
                })
            else:
                return JsonResponse({'error': 'Invalid status'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def my_assignments(request):
    """View for current user's assignments"""
    assignments = WorkAssignment.objects.filter(
        assigned_to=request.user
    ).select_related('intervention', 'vehicle').prefetch_related('assigned_to').order_by('-created_at')
    
    # Separate by status
    pending_assignments = assignments.filter(status='pending')
    active_assignments = assignments.filter(status__in=['assigned', 'in_progress'])
    completed_worked_assignments = assignments.filter(status='completed')
    completed_not_worked_assignments = assignments.filter(status='not_worked')
    cancelled_assignments = assignments.filter(status='cancelled')
    
    context = {
        'title': 'My Assignments',
        'pending_assignments': pending_assignments,
        'active_assignments': active_assignments,
        'completed_worked_assignments': completed_worked_assignments,
        'completed_not_worked_assignments': completed_not_worked_assignments,
        'cancelled_assignments': cancelled_assignments,
        'stats': {
            'total': assignments.count(),
            'pending': pending_assignments.count(),
            'active': active_assignments.count(),
            'completed_worked': completed_worked_assignments.count(),
            'completed_not_worked': completed_not_worked_assignments.count(),
            'cancelled': cancelled_assignments.count(),
        }
    }
    
    return render(request, 'assignments/my_assignments.html', context)


@login_required
def create_assignment_from_intervention(request, intervention_id):
    """Create assignment directly from intervention"""
    intervention = get_object_or_404(Intervention, pk=intervention_id)
    
    if request.method == 'POST':
        # Create a mutable copy of POST data and add the intervention
        post_data = request.POST.copy()
        post_data['intervention'] = str(intervention.pk)
        
        form = WorkAssignmentForm(post_data, user=request.user)
        if form.is_valid():
            # Set the intervention
            assignment = form.save(commit=False)
            assignment.intervention = intervention
            assignment.created_by = request.user
            assignment.save()
            form.save_m2m()
            
            messages.success(request, f'Assignment created for {intervention.codice_nigit}')
            return redirect('assignments:assignment-detail', pk=assignment.pk)
    else:
        # Pre-fill form with intervention code
        form = WorkAssignmentForm(user=request.user, initial={'codice_nigit_input': intervention.codice_nigit})
    
    context = {
        'title': f'Assign Work: {intervention.codice_nigit}',
        'form': form,
        'intervention': intervention,
        'action': 'create_from_intervention'
    }
    
    return render(request, 'assignments/assignment_form.html', context)


@login_required
def delete_assignment(request, pk):
    """Delete assignment"""
    assignment = get_object_or_404(WorkAssignment, pk=pk)
    
    # Handle both GET and POST for deletion
    try:
        assignment_code = assignment.codice_nigit
        assignment.delete()
        messages.success(request, f'Assignment {assignment_code} has been deleted successfully')
        return redirect('assignments:assignment-list')
    except Exception as e:
        messages.error(request, f'Error deleting assignment: {str(e)}')
        return redirect('assignments:assignment-list')
