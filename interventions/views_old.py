from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from .models import Intervention
from accounts.permissions import role_required, user_is_assigned_to_intervention, get_user_role
from reports.models import Report
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from fleet.models import Car, CarUsage


@login_required
def intervention_list(request):
    role = get_user_role(request.user)
    if role == "technician":
        interventions = Intervention.objects.filter(assigned_employees=request.user).order_by("-created_at")
    elif role in {"superadmin", "admin", "warehouse", "hr"}:
        interventions = Intervention.objects.all().order_by("-created_at")
    else:
        raise PermissionDenied("You do not have permission to view interventions.")
    
    # Calculate counts for stats
    in_progress_count = interventions.filter(status="in_progress").count()
    finished_count = interventions.filter(status="finished").count()
    not_confirmed_count = interventions.filter(status="not_confirmed").count()
    
    return render(request, 'interventions/list.html', {
        'interventions': interventions,
        'in_progress_count': in_progress_count,
        'finished_count': finished_count,
        'not_confirmed_count': not_confirmed_count,
    })


@login_required
@role_required("superadmin", "admin")
def intervention_create(request):
    employees = User.objects.all()
    cars = Car.objects.all().order_by("plate_number")

    if request.method == 'POST':
        client = request.POST.get('client_name', '').strip()
        region = request.POST.get('region', '').strip()
        description = request.POST.get('description', '').strip()
        employee_ids = request.POST.getlist('employees')
        car_id = request.POST.get('car', '').strip()

        # Model's `save()` will generate `code` when it's empty.
        intervention = Intervention.objects.create(
            code='',
            client=client,
            intervention_type='correttiva',  # Default type
            status='not_confirmed',  # Default status
        )
        if employee_ids:
            intervention.data = {'assigned_employee_ids': employee_ids}

        if car_id:
            # Track which car was used for this job.
            CarUsage.objects.get_or_create(
                car_id=car_id,
                intervention=intervention,
                employee=request.user,
                date=timezone.localdate(),
            )

        return redirect('/interventions/')

    return render(request, 'interventions/create.html', {'employees': employees, 'cars': cars})


@login_required
@role_required("superadmin", "admin", "warehouse", "hr", "technician")
def intervention_detail(request, pk):
    intervention = get_object_or_404(Intervention, pk=pk)
    if get_user_role(request.user) == "technician" and not user_is_assigned_to_intervention(request.user, intervention):
        raise PermissionDenied("You are not assigned to this intervention.")
    return render(request, 'interventions/detail.html', {'i': intervention})


@login_required
@role_required("superadmin", "admin")
def intervention_delete(request, pk):
    intervention = get_object_or_404(Intervention, pk=pk)
    intervention.delete()
    return redirect('/interventions/')


@login_required
@role_required("superadmin", "admin", "technician")
def intervention_status(request, pk, status):
    intervention = get_object_or_404(Intervention, pk=pk)

    role = get_user_role(request.user)

    allowed_statuses = {key for key, _label in Intervention.STATUS_CHOICES}
    if status not in allowed_statuses:
        raise PermissionDenied("Invalid status.")

    # Option 1-A rules:
    # - Start: Admin always; Technician only if assigned
    # - Finish: Admin always; Technician only if a report exists
    if status == "in_progress":
        # Transition: not_confirmed -> in_progress
        if intervention.status != "not_confirmed":
            raise PermissionDenied("You cannot start an intervention from its current status.")
        if role in {"superadmin", "admin"}:
            pass
        elif role == "technician" and user_is_assigned_to_intervention(request.user, intervention):
            pass
        else:
            raise PermissionDenied("You cannot start this intervention.")

    elif status == "finished":
        # Transition: in_progress -> finished
        if intervention.status != "in_progress":
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

    # Keep not_confirmed transitions blocked by default.
    elif status == "not_confirmed":
        raise PermissionDenied("You cannot revert status.")

    intervention.status = status
    intervention.save(update_fields=["status"])
    return redirect('/interventions/')


@login_required
@role_required("superadmin", "admin")
def intervention_edit(request, pk):
    intervention = get_object_or_404(Intervention, pk=pk)
    employees = User.objects.all()
    cars = Car.objects.all().order_by("plate_number")

    if request.method == 'POST':
        intervention.client = request.POST.get('client_name', '').strip()
        additional_data = intervention.data or {}
        additional_data['region'] = request.POST.get('region', '').strip()
        additional_data['description'] = request.POST.get('description', '').strip()
        additional_data['car_id'] = request.POST.get('car', '').strip()
        intervention.data = additional_data
        
        car_id = request.POST.get('car', '').strip()
        employee_ids = request.POST.getlist('employees')
        
        if employee_ids:
            intervention.data['assigned_employee_ids'] = employee_ids
        
        intervention.save(update_fields=["client", "data"])

        if car_id:
            CarUsage.objects.get_or_create(
                car_id=car_id,
                intervention=intervention,
                employee=request.user,
                date=timezone.localdate(),
            )
        return redirect('/interventions/')

    return render(
        request,
        'interventions/edit.html',
        {
            'i': intervention,
            'employees': employees,
            'cars': cars,
        },
    )