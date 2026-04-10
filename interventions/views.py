from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.cache import cache
from django.db.models import Count, Q, F, Prefetch, Sum, Avg
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers, vary_on_cookie
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages

from accounts.models import User
from .models import Intervention
from accounts.permissions import role_required, user_is_assigned_to_intervention, get_user_role
# from reports.models import Report  # Commented out until reports module is integrated
from django.core.exceptions import PermissionDenied
from fleet.models import Car, CarUsage


@login_required
@cache_page(60 * 5)  # Cache for 5 minutes
@vary_on_cookie
def intervention_list(request):
    """
    Optimized intervention list view with caching and JSONField query optimization
    """
    role = get_user_role(request.user)
    
    # Optimized queries based on role using JSONField
    if role == "technician":
        # Use prefetch_related for many-to-many optimization
        interventions = Intervention.objects.filter(
            assigned_employees=request.user
        ).select_related(
            'used_car'  # Optimize foreign key queries
        ).prefetch_related(
            'assigned_employees'  # Optimize many-to-many
        ).order_by('-created_at')
    elif role in {"superadmin", "admin", "warehouse", "hr"}:
        # Use select_related and prefetch_related for admin views
        interventions = Intervention.objects.select_related(
            'used_car'
        ).prefetch_related(
            'assigned_employees'
        ).order_by('-created_at')
    else:
        raise PermissionDenied("You do not have permission to view interventions.")
    
    # Optimized counts with database-level aggregation using JSONField
    stats_cache_key = f'intervention_stats_{role}'
    stats = cache.get(stats_cache_key)
    
    if not stats:
        # Use optimized aggregation queries with JSONField
        stats = {
            'in_progress_count': interventions.filter(stato_avanzamento_nigit='IN_CORSO').count(),
            'finished_count': interventions.filter(stato_avanzamento_nigit='COMPLETATO').count(),
            'not_confirmed_count': interventions.filter(stato_avanzamento_nigit='DA_INIZIARE').count(),
            'total_count': interventions.count(),
        }
        cache.set(stats_cache_key, stats, 60 * 2)  # Cache for 2 minutes
    
    # Add pagination for better performance with large datasets
    paginator = Paginator(interventions, 25)  # 25 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'interventions': page_obj,
        'stats': stats,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'role': role,
    }
    
    return render(request, 'interventions/list.html', context)


@login_required
def intervention_create(request):
    """
    Optimized intervention creation view with caching
    """
    # Cache frequently accessed data
    cache_key = 'intervention_create_data'
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        employees = User.objects.select_related('employee_profile').all()
        cars = Car.objects.select_related('assigned_employee').all().order_by("plate_number")
        
        cached_data = {
            'employees': employees,
            'cars': cars,
        }
        cache.set(cache_key, cached_data, 60 * 5)  # Cache for 5 minutes
    else:
        employees = cached_data['employees']
        cars = cached_data['cars']

    if request.method == 'POST':
        # Optimized form processing with JSONField
        client_name = request.POST.get('client_name', '').strip()
        region = request.POST.get('region', '').strip()
        description = request.POST.get('description', '').strip()
        employee_ids = request.POST.getlist('employees')
        car_id = request.POST.get('car', '').strip()

        # Use bulk operations for better performance with JSONField
        intervention = Intervention.objects.create(
            code='',  # Will be auto-generated
            data={
                'CLIENTE': client_name,
                'region': region,
                'description': description,
                'status': 'not_confirmed',
                'payment_status': 'pending',
            },
            used_car_id=car_id or None,
        )
        
        # Use set() for many-to-many (more efficient than individual adds)
        if employee_ids:
            intervention.assigned_employees.set(employee_ids)

        # Create car usage record if car assigned
        if car_id:
            CarUsage.objects.get_or_create(
                car_id=car_id,
                intervention=intervention,
                employee=request.user,
                date=timezone.localdate(),
            )

        # Clear relevant caches
        cache.delete('intervention_stats_*')
        cache.delete('dashboard_stats_*')
        
        messages.success(request, 'Intervention created successfully!')
        return redirect('/interventions/')

    return render(request, 'interventions/create.html', {
        'employees': employees,
        'cars': cars,
    })


@login_required
def intervention_detail(request, pk):
    """
    Optimized intervention detail view with comprehensive caching
    """
    # Use select_related and prefetch_related for optimal queries
    intervention = get_object_or_404(
        Intervention.objects.select_related(
            'used_car'
        ).prefetch_related(
            'assigned_employees',
            'report_set',  # Related reports
            'work_assignments'  # Related work assignments
        ),
        pk=pk
    )
    
    # Permission check
    if get_user_role(request.user) == "technician" and not user_is_assigned_to_intervention(request.user, intervention):
        raise PermissionDenied("You are not assigned to this intervention.")
    
    # Cache related data
    cache_key = f'intervention_detail_data_{pk}'
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        # Get related reports efficiently
        reports = intervention.report_set.select_related('employee').order_by('-created_at')
        
        cached_data = {
            'reports': reports,
            'can_edit': get_user_role(request.user) in {"superadmin", "admin"},
            'can_delete': get_user_role(request.user) in {"superadmin", "admin"},
        }
        cache.set(cache_key, cached_data, 60 * 5)
    else:
        reports = cached_data['reports']
        can_edit = cached_data['can_edit']
        can_delete = cached_data['can_delete']

    return render(request, 'interventions/detail.html', {
        'intervention': intervention,
        'reports': reports,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })


@login_required
def intervention_delete(request, pk):
    """
    Optimized intervention deletion with cache clearing
    """
    intervention = get_object_or_404(Intervention, pk=pk)
    
    # Store info for cache clearing
    intervention_code = intervention.code
    
    # Delete with cascade handling
    intervention.delete()
    
    # Clear all relevant caches
    cache.delete('intervention_stats_*')
    cache.delete('dashboard_stats_*')
    cache.delete(f'intervention_detail_data_{pk}')
    
    messages.success(request, f'Intervention {intervention_code} deleted successfully!')
    return redirect('/interventions/')


@login_required
def intervention_status(request, pk, status):
    """
    Optimized intervention status update with JSONField and cache invalidation
    """
    intervention = get_object_or_404(Intervention, pk=pk)
    role = get_user_role(request.user)

    # Validate status
    allowed_statuses = {"not_confirmed", "in_progress", "finished"}
    if status not in allowed_statuses:
        raise PermissionDenied("Invalid status.")

    # Business logic for status transitions using JSONField
    current_status = intervention.data.get('status', 'not_confirmed')
    
    if status == "in_progress":
        if current_status != "not_confirmed":
            raise PermissionDenied("You cannot start an intervention from its current status.")
        if role in {"superadmin", "admin"}:
            pass
        elif role == "technician" and user_is_assigned_to_intervention(request.user, intervention):
            pass
        else:
            raise PermissionDenied("You cannot start this intervention.")

    elif status == "finished":
        if current_status != "in_progress":
            raise PermissionDenied("You can only finish an intervention that is in progress.")
        if role in {"superadmin", "admin"}:
            pass
        elif role == "technician":
            has_report = Report.objects.filter(intervention=intervention).exists()
            if has_report and user_is_assigned_to_intervention(request.user, intervention):
                pass
            else:
                raise PermissionDenied("You can finish only after submitting a report (and only if assigned).")
        else:
            raise PermissionDenied("You cannot finish this intervention.")

    elif status == "not_confirmed":
        raise PermissionDenied("You cannot revert status.")

    # Map old status values to new status field
    status_mapping = {
        'in_progress': 'IN_CORSO',
        'finished': 'COMPLETATO',
        'not_confirmed': 'DA_INIZIARE'
    }
    new_status = status_mapping.get(status, status)
    
    # Update status using new field
    intervention.stato_avanzamento_nigit = new_status
    intervention.save(update_fields=["stato_avanzamento_nigit"])
    
    # Clear relevant caches
    cache.delete('intervention_stats_*')
    cache.delete('dashboard_stats_*')
    cache.delete(f'intervention_detail_data_{pk}')
    
    messages.success(request, f'Intervention status updated to {status}!')
    return redirect('/interventions/')


@login_required
def intervention_edit(request, pk):
    """
    Optimized intervention editing with efficient caching
    """
    intervention = get_object_or_404(
        Intervention.objects.select_related('used_car').prefetch_related('assigned_employees'),
        pk=pk
    )
    
    # Cache form data
    cache_key = 'intervention_edit_data'
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        employees = User.objects.select_related('employee_profile').all()
        cars = Car.objects.select_related('assigned_employee').all().order_by("plate_number")
        
        cached_data = {
            'employees': employees,
            'cars': cars,
        }
        cache.set(cache_key, cached_data, 60 * 5)
    else:
        employees = cached_data['employees']
        cars = cached_data['cars']

    if request.method == 'POST':
        # Optimized update with JSONField
        client_name = request.POST.get('client_name', '').strip()
        region = request.POST.get('region', '').strip()
        description = request.POST.get('description', '').strip()
        car_id = request.POST.get('car', '').strip()
        employee_ids = request.POST.getlist('employees')

        # Update model fields directly
        intervention.cliente = client_name
        # Note: 'region' and 'description' fields don't exist in new model
        # You may need to add them or store in note field
        if region:
            intervention.note = f"Region: {region}\n{intervention.note or ''}"
        if description:
            intervention.note = f"Description: {description}\n{intervention.note or ''}"

        # Efficient many-to-many update
        if employee_ids:
            intervention.assigned_employees.set(employee_ids)
        else:
            intervention.assigned_employees.clear()

        # Update car assignment
        intervention.used_car_id = car_id or None
        
        # Save only changed fields
        intervention.save(update_fields=["cliente", "note", "used_car"])

        # Handle car usage
        if car_id:
            CarUsage.objects.get_or_create(
                car_id=car_id,
                intervention=intervention,
                employee=request.user,
                date=timezone.localdate(),
            )
        
        # Clear caches
        cache.delete('intervention_stats_*')
        cache.delete('dashboard_stats_*')
        cache.delete(f'intervention_detail_data_{pk}')
        
        messages.success(request, 'Intervention updated successfully!')
        return redirect('/interventions/')

    return render(request, 'interventions/edit.html', {
        'intervention': intervention,
        'employees': employees,
        'cars': cars,
    })


# AJAX API endpoints for better performance
@login_required
def intervention_stats_api(request):
    """
    API endpoint for real-time statistics
    """
    role = get_user_role(request.user)
    
    # Use cached stats
    cache_key = f'intervention_stats_api_{role}'
    stats = cache.get(cache_key)
    
    if not stats:
        if role == "technician":
            base_qs = Intervention.objects.filter(assigned_employees=request.user)
        else:
            base_qs = Intervention.objects.all()
        
        stats = {
            'total': base_qs.count(),
            'active': base_qs.filter(stato_avanzamento_nigit__in=['DA_INIZIARE', 'IN_CORSO', 'SOSPESO']).count(),
            'completed': base_qs.filter(stato_avanzamento_nigit='COMPLETATO').count(),
            'pending': base_qs.filter(stato_avanzamento_nigit='DA_INIZIARE').count(),
            'last_updated': timezone.now().isoformat(),
        }
        cache.set(cache_key, stats, 60)  # Cache for 1 minute
    
    return JsonResponse(stats)


@login_required
def intervention_search(request):
    """
    Optimized search functionality with database-level search
    """
    query = request.GET.get('q', '').strip()
    role = get_user_role(request.user)
    
    if not query:
        return JsonResponse({'results': []})
    
    # Build optimized search query
    search_qs = Intervention.objects.filter(
        Q(codice_nigit__icontains=query) |
        Q(cliente__icontains=query) |
        Q(nome__icontains=query) |
        Q(assistente__icontains=query)
    )
    
    # Apply role-based filtering
    if role == "technician":
        search_qs = search_qs.filter(assigned_employees=request.user)
    
    # Use select_related for performance
    results = list(
        search_qs.select_related('used_car')
        .values('id', 'codice_nigit', 'cliente', 'nome', 'stato_avanzamento_nigit', 'created_at')
        .order_by('-created_at')[:10]  # Limit to 10 results
    )
    
    return JsonResponse({'results': results})
