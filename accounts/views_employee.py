from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .forms_extended import (
    EmployeeCreateForm, EmployeeEditForm, EmployeeProfileForm,
    EmployeeDocumentForm, EmployeeSkillForm, EmployeeAssetForm, DepartmentForm
)
from .models import EmployeeProfile, EmployeeDocument, EmployeeSkill, EmployeeAsset, Department

User = get_user_model()


def is_superuser_or_staff(user):
    """Check if user is superuser or staff"""
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_superuser_or_staff)
def employee_list(request):
    """View for listing all employees with search and filtering"""
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    role_filter = request.GET.get('role', '')
    
    # Exclude ex-employees from the active employees list
    employees = User.objects.filter(is_active=True).exclude(role=User.Role.EX_EMPLOYEE).select_related('profile').order_by('first_name', 'last_name')
    
    # Apply filters
    if search_query:
        employees = employees.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )
    
    if department_filter:
        employees = employees.filter(department__icontains=department_filter)
    
    if role_filter:
        employees = employees.filter(role=role_filter)
    
    # Pagination
    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get departments for filter dropdown
    departments = User.objects.values_list('department', flat=True).distinct()
    departments = [dept for dept in departments if dept]
    
    context = {
        'title': 'Employees',
        'employees': page_obj,
        'search_query': search_query,
        'department_filter': department_filter,
        'role_filter': role_filter,
        'departments': departments,
        'roles': User.Role.choices,
        'inactive_employees': User.objects.filter(is_active=False, is_superuser=False).count(),
    }
    return render(request, 'accounts/employee_list.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def employee_archive(request):
    """View for listing archived employees (ex-employees)"""
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    
    # Get inactive employees (is_active=False)
    archived_employees = User.objects.filter(is_active=False, is_superuser=False).select_related('profile').order_by('first_name', 'last_name')
    
    # Apply filters
    if search_query:
        archived_employees = archived_employees.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )
    
    if department_filter:
        archived_employees = archived_employees.filter(department__icontains=department_filter)
    
    # Pagination
    paginator = Paginator(archived_employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get departments for filter dropdown
    departments = User.objects.values_list('department', flat=True).distinct()
    departments = [dept for dept in departments if dept]
    
    context = {
        'title': 'Employee Archive',
        'employees': page_obj,
        'search_query': search_query,
        'department_filter': department_filter,
        'departments': departments,
        'is_archive': True,
        'inactive_employees': archived_employees.count(),
    }
    return render(request, 'accounts/employee_list.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def employee_detail(request, pk):
    """View for employee details with comprehensive information"""
    employee = get_object_or_404(User, pk=pk)
    
    # Get or create employee profile
    profile, created = EmployeeProfile.objects.get_or_create(user=employee)
    
    # Get employee's assignments
    try:
        from assignments.models import WorkAssignment
        employee_assignments = WorkAssignment.objects.filter(
            assigned_to=employee
        ).select_related('intervention').order_by('-created_at')[:10]
    except ImportError:
        employee_assignments = []
    
    # Get employee's attendance records
    try:
        from attendance.models import Attendance
        employee_attendance = Attendance.objects.filter(
            user=employee
        ).order_by('-date')[:10]
    except ImportError:
        employee_attendance = []
    
    # Get employee's documents
    documents = EmployeeDocument.objects.filter(employee=employee).order_by('-upload_date')
    
    # Get employee's skills
    skills = EmployeeSkill.objects.filter(employee=employee).order_by('-years_of_experience')
    
    # Get employee's assets
    assets = EmployeeAsset.objects.filter(employee=employee, is_returned=False).order_by('-allocation_date')
    
    context = {
        'title': f'Employee: {employee.get_full_name() or employee.username}',
        'employee': employee,
        'profile': profile,
        'employee_assignments': employee_assignments,
        'employee_attendance': employee_attendance,
        'documents': documents,
        'skills': skills,
        'assets': assets,
    }
    return render(request, 'accounts/employee_detail_comprehensive.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def employee_create(request):
    """View for creating new employee"""
    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            employee = form.save()
            # Create empty profile for the employee
            EmployeeProfile.objects.create(user=employee)
            messages.success(request, f'Employee {employee.get_full_name() or employee.username} has been created successfully.')
            return redirect('accounts:employee-detail', employee.pk)
    else:
        form = EmployeeCreateForm()
    
    context = {
        'title': 'Create New Employee',
        'form': form,
        'action': 'create'
    }
    return render(request, 'accounts/employee_form.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def employee_edit(request, pk):
    """View for editing existing employee"""
    employee = get_object_or_404(User, pk=pk)
    profile, created = EmployeeProfile.objects.get_or_create(user=employee)
    
    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'Employee {employee.get_full_name() or employee.username} has been updated successfully.')
            return redirect('accounts:employee-detail', employee.pk)
    else:
        form = EmployeeEditForm(instance=employee)
    
    context = {
        'title': f'Edit Employee: {employee.get_full_name() or employee.username}',
        'form': form,
        'employee': employee,
        'action': 'edit'
    }
    return render(request, 'accounts/employee_form.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def employee_profile_edit(request, pk):
    """View for editing employee profile information"""
    employee = get_object_or_404(User, pk=pk)
    profile, created = EmployeeProfile.objects.get_or_create(user=employee)
    
    if request.method == 'POST':
        # Check which form was submitted
        if 'basic_info' in request.POST:
            basic_form = EmployeeEditForm(request.POST, instance=employee)
            if basic_form.is_valid():
                basic_form.save()
                messages.success(request, f'Basic information for {employee.get_full_name() or employee.username} has been updated successfully.')
                return redirect('accounts:employee-detail', employee.pk)
        else:
            # Profile form submitted
            form = EmployeeProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, f'Profile for {employee.get_full_name() or employee.username} has been updated successfully.')
                return redirect('accounts:employee-detail', employee.pk)
    else:
        basic_form = EmployeeEditForm(instance=employee)
        form = EmployeeProfileForm(instance=profile)
    
    context = {
        'title': f'Edit Profile: {employee.get_full_name() or employee.username}',
        'form': form,
        'basic_form': basic_form,
        'employee': employee,
        'profile': profile,
    }
    return render(request, 'accounts/employee_profile_form.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def employee_documents(request, pk):
    """View for managing employee documents"""
    employee = get_object_or_404(User, pk=pk)
    documents = EmployeeDocument.objects.filter(employee=employee).order_by('-upload_date')
    
    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee = employee
            document.save()
            messages.success(request, f'Document "{document.title}" has been uploaded successfully.')
            return redirect('accounts:employee-documents', employee.pk)
    else:
        form = EmployeeDocumentForm()
    
    context = {
        'title': f'Documents: {employee.get_full_name() or employee.username}',
        'employee': employee,
        'documents': documents,
        'form': form,
    }
    return render(request, 'accounts/employee_documents.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def employee_skills(request, pk):
    """View for managing employee skills"""
    employee = get_object_or_404(User, pk=pk)
    skills = EmployeeSkill.objects.filter(employee=employee).order_by('-years_of_experience')
    
    if request.method == 'POST':
        form = EmployeeSkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.employee = employee
            skill.save()
            messages.success(request, f'Skill "{skill.skill_name}" has been added successfully.')
            return redirect('accounts:employee-skills', employee.pk)
    else:
        form = EmployeeSkillForm()
    
    context = {
        'title': f'Skills: {employee.get_full_name() or employee.username}',
        'employee': employee,
        'skills': skills,
        'form': form,
    }
    return render(request, 'accounts/employee_skills.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def employee_assets(request, pk):
    """View for managing employee assets"""
    employee = get_object_or_404(User, pk=pk)
    assets = EmployeeAsset.objects.filter(employee=employee).order_by('-allocation_date')
    
    if request.method == 'POST':
        form = EmployeeAssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.employee = employee
            asset.save()
            messages.success(request, f'Asset "{asset.asset_name}" has been allocated successfully.')
            return redirect('accounts:employee-assets', employee.pk)
    else:
        form = EmployeeAssetForm()
    
    context = {
        'title': f'Assets: {employee.get_full_name() or employee.username}',
        'employee': employee,
        'assets': assets,
        'form': form,
    }
    return render(request, 'accounts/employee_assets.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def department_list(request):
    """View for listing departments"""
    departments = Department.objects.all().select_related('manager', 'parent').order_by('name')
    
    context = {
        'title': 'Departments',
        'departments': departments,
    }
    return render(request, 'accounts/department_list.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def department_create(request):
    """View for creating new department"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department "{department.name}" has been created successfully.')
            return redirect('accounts:department-list')
    else:
        form = DepartmentForm()
    
    context = {
        'title': 'Create Department',
        'form': form,
    }
    return render(request, 'accounts/department_form.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def department_edit(request, pk):
    """View for editing existing department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department "{department.name}" has been updated successfully.')
            return redirect('accounts:department-list')
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'title': f'Edit Department: {department.name}',
        'form': form,
        'department': department,
    }
    return render(request, 'accounts/department_form.html', context)


@login_required
@user_passes_test(is_superuser_or_staff)
def document_verify(request, employee_pk, doc_pk):
    """Verify employee document"""
    document = get_object_or_404(EmployeeDocument, pk=doc_pk, employee__pk=employee_pk)
    
    if request.method == 'POST':
        document.is_verified = True
        document.verified_by = request.user
        document.verified_date = timezone.now()
        document.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Document "{document.title}" has been verified successfully.'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed.'
    })


@login_required
@user_passes_test(is_superuser_or_staff)
def document_delete(request, employee_pk, doc_pk):
    """Delete employee document"""
    document = get_object_or_404(EmployeeDocument, pk=doc_pk, employee__pk=employee_pk)
    
    if request.method == 'POST':
        document_title = document.title
        document.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Document "{document_title}" has been deleted successfully.'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed.'
    })


@login_required
@user_passes_test(is_superuser_or_staff)
def skill_delete(request, employee_pk, skill_pk):
    """Delete employee skill"""
    skill = get_object_or_404(EmployeeSkill, pk=skill_pk, employee__pk=employee_pk)
    
    if request.method == 'POST':
        skill_name = skill.skill_name
        skill.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Skill "{skill_name}" has been deleted successfully.'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed.'
    })


@login_required
@user_passes_test(is_superuser_or_staff)
def asset_return(request, employee_pk, asset_pk):
    """Mark employee asset as returned"""
    asset = get_object_or_404(EmployeeAsset, pk=asset_pk, employee__pk=employee_pk)
    
    if request.method == 'POST':
        asset.is_returned = True
        asset.return_date = timezone.now().date()
        asset.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Asset "{asset.asset_name}" has been marked as returned.'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed.'
    })


@login_required
@user_passes_test(is_superuser_or_staff)
def asset_delete(request, employee_pk, asset_pk):
    """Delete employee asset"""
    asset = get_object_or_404(EmployeeAsset, pk=asset_pk, employee__pk=employee_pk)
    
    if request.method == 'POST':
        asset_name = asset.asset_name
        asset.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Asset "{asset_name}" has been deleted successfully.'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed.'
    })
