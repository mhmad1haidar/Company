from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from .models import WorkAssignment

User = get_user_model()

def is_admin_or_manager(user):
    """Check if user is admin or has manager permissions"""
    return user.is_superuser or user.has_perm('assignments.view_all_assignments')

@login_required
def admin_dashboard(request):
    """Admin dashboard showing assignments grouped by user"""
    
    # Get all users with assignments
    users_with_assignments = User.objects.filter(
        work_assignments__isnull=False
    ).distinct().annotate(
        assignment_count=Count('work_assignments'),
        pending_count=Count('work_assignments', filter=Q(work_assignments__status='pending')),
        in_progress_count=Count('work_assignments', filter=Q(work_assignments__status='in_progress')),
        completed_count=Count('work_assignments', filter=Q(work_assignments__status='completed'))
    ).order_by('first_name', 'last_name')
    
    # Get recent assignments for each user
    user_assignments = {}
    for user in users_with_assignments:
        recent_assignments = WorkAssignment.objects.filter(
            assigned_to=user
        ).select_related(
            'intervention'
        ).prefetch_related(
            'assigned_to'
        ).order_by('-assigned_date')[:5]
        user_assignments[user.id] = recent_assignments
    
    # Statistics
    total_assignments = WorkAssignment.objects.count()
    active_assignments = WorkAssignment.objects.filter(
        status__in=['pending', 'assigned', 'in_progress']
    ).count()
    completed_assignments = WorkAssignment.objects.filter(status='completed').count()
    
    context = {
        'users_with_assignments': users_with_assignments,
        'user_assignments': user_assignments,
        'total_assignments': total_assignments,
        'active_assignments': active_assignments,
        'completed_assignments': completed_assignments,
    }
    
    return render(request, 'assignments/admin_dashboard.html', context)
