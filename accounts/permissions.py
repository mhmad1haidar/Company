from functools import wraps
from django.core.exceptions import PermissionDenied


def get_user_role(user) -> str | None:
    """
    Normalizes role coming from custom User model.
    Superusers are treated as superadmin.
    """
    if getattr(user, "is_superuser", False):
        return "superadmin"
    role = getattr(user, "role", None)
    if not role:
        # Backwards-compatible fallback for existing users while roles are being set up.
        if getattr(user, "is_staff", False):
            return "admin"
        return "technician"
    return role


def has_permission(user, permission_codename):
    """Check if user has specific permission"""
    if user.is_superuser:
        return True
    
    role_permissions = {
        'hr': [
            'view_employees', 'add_employee', 'change_employee', 'delete_employee',
            'view_attendance', 'add_attendance', 'change_attendance',
        ],
        'warehouse': [
            'view_warehouse', 'add_warehouse', 'change_warehouse', 'delete_warehouse',
            'view_attendance', 'add_attendance', 'change_attendance',
        ],
        'admin': [
            'view_employees', 'add_employee', 'change_employee', 'delete_employee',
            'view_warehouse', 'add_warehouse', 'change_warehouse', 'delete_warehouse',
            'view_attendance', 'add_attendance', 'change_attendance',
            'view_interventions', 'add_intervention', 'change_intervention', 'delete_intervention',
        ],
        'superadmin': [
            'view_employees', 'add_employee', 'change_employee', 'delete_employee',
            'view_warehouse', 'add_warehouse', 'change_warehouse', 'delete_warehouse',
            'view_attendance', 'add_attendance', 'change_attendance', 'delete_attendance',
            'view_interventions', 'add_intervention', 'change_intervention', 'delete_intervention',
            'view_reports', 'add_report', 'change_report', 'delete_report',
            'view_fleet', 'add_car', 'change_car', 'delete_car',
        ],
        'technician': [
            'view_interventions', 'change_intervention',
            'view_attendance', 'add_attendance', 'change_attendance',
        ],
    }
    
    return permission_codename in role_permissions.get(get_user_role(user), [])


def permission_required(permission_codename):
    """Decorator to require specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            if not has_permission(request.user, permission_codename):
                raise PermissionDenied("You don't have permission to access this page.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def role_required(*allowed_roles: str):
    """
    Decorator for role-based access control.
    Raises 403 if role is not allowed.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            role = get_user_role(request.user)
            if role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this page.")

        return _wrapped_view

    return decorator


def user_is_assigned_to_intervention(user, intervention) -> bool:
    """
    Technician access is based on intervention assignment.
    Admin and superadmin can access all interventions.
    """
    if not user or not getattr(user, "id", None):
        return False
    
    role = get_user_role(user)
    if role in ['superadmin', 'admin']:
        return True
    
    return intervention.assigned_employees.filter(id=user.id).exists()


def get_accessible_modules(user):
    """Get list of modules user can access"""
    role = get_user_role(user)
    
    modules = {
        'hr': ['employees', 'attendance'],
        'warehouse': ['warehouse', 'attendance'],
        'admin': ['employees', 'warehouse', 'attendance', 'interventions'],
        'superadmin': ['employees', 'warehouse', 'attendance', 'interventions', 'reports', 'fleet'],
        'technician': ['interventions', 'attendance'],
    }
    
    return modules.get(role, [])


def can_view_all_attendance(user):
    """Check if user can view all attendance records"""
    role = get_user_role(user)
    return role in ['superadmin', 'hr', 'warehouse', 'admin']


def can_view_own_attendance_only(user):
    """Check if user can only view their own attendance"""
    role = get_user_role(user)
    return role in ['technician']
