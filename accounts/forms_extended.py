from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import EmployeeProfile, EmployeeDocument, EmployeeSkill, EmployeeAsset, Department, Certification

User = get_user_model()


class EmployeeCreateForm(UserCreationForm):
    """Form for creating new employees with extended profile"""
    
    class Meta:
        model = User
        fields = [
            'username', 'password1', 'password2', 'email', 'first_name', 'last_name',
            'role', 'employee_id', 'department', 'job_title', 'is_staff', 'is_active'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        
        # Add custom labels
        self.fields['username'].label = 'Username *'
        self.fields['email'].label = 'Email Address *'
        self.fields['first_name'].label = 'First Name'
        self.fields['last_name'].label = 'Last Name'
        self.fields['role'].label = 'Role'
        self.fields['employee_id'].label = 'Employee ID'
        self.fields['job_title'].label = 'Job Title'
        self.fields['is_staff'].label = 'Staff Access (can manage employees)'
        self.fields['is_active'].label = 'Active Account'
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        # For create form, set default role if not specified
        if not employee.role:
            employee.role = User.Role.EMPLOYEE
        if commit:
            employee.save()
        return employee


class EmployeeEditForm(forms.ModelForm):
    """Form for editing existing employees"""
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'employee_id', 'job_title', 'is_staff', 'is_superuser', 'is_active'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom labels
        self.fields['username'].label = 'Username *'
        self.fields['email'].label = 'Email Address *'
        self.fields['first_name'].label = 'First Name'
        self.fields['last_name'].label = 'Last Name'
        self.fields['role'].label = 'Role'
        self.fields['employee_id'].label = 'Employee ID'
        self.fields['job_title'].label = 'Job Title'
        self.fields['is_staff'].label = 'Staff Access (can manage employees)'
        self.fields['is_superuser'].label = 'Superuser (full admin access)'
        self.fields['is_active'].label = 'Active Account'
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        
        # Handle role-based activation/deactivation
        if employee.role == User.Role.EX_EMPLOYEE:
            # Deactivate when role is ex_employee
            employee.is_active = False
            employee.is_staff = False
            employee.is_superuser = False
        elif self.instance.pk and self.instance.role == User.Role.EX_EMPLOYEE and employee.role != User.Role.EX_EMPLOYEE:
            # Reactivate when changing from ex_employee to another role
            employee.is_active = True
        elif self.instance.pk and self.instance.role != User.Role.EX_EMPLOYEE and employee.role == User.Role.EX_EMPLOYEE:
            # Deactivate when changing to ex_employee
            employee.is_active = False
            employee.is_staff = False
            employee.is_superuser = False
        elif self.instance.pk and employee.role in [User.Role.EMPLOYEE, User.Role.MANAGER, User.Role.ADMIN] and employee.is_active == False:
            # Auto-activate when role is set to an active role
            employee.is_active = True
        
        # Handle manual is_active toggle - if user manually activates an ex-employee, change role to employee
        if self.instance.pk and self.instance.is_active == False and employee.is_active == True and employee.role == User.Role.EX_EMPLOYEE:
            employee.role = User.Role.EMPLOYEE
        
        if commit:
            employee.save()
        return employee


class EmployeeProfileForm(forms.ModelForm):
    """Form for extended employee profile information"""
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'date_of_birth', 'gender', 'blood_group',
            'personal_phone', 'work_phone', 'emergency_contact_name', 
            'emergency_contact_phone', 'emergency_contact_relation',
            'current_address', 'permanent_address', 'city', 'state', 
            'country', 'postal_code', 'hire_date', 'employment_type',
            'work_location', 'reporting_manager', 'bank_name', 
            'bank_account_number', 'bank_ifsc_code', 'salary',
            'nationality', 'marital_status', 'passport_number', 'visa_status'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'personal_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'work_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'current_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'permanent_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'work_location': forms.TextInput(attrs={'class': 'form-control'}),
            'reporting_manager': forms.Select(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_ifsc_code': forms.TextInput(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'marital_status': forms.Select(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
            'visa_status': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter reporting manager to exclude current user
        if 'instance' in kwargs and kwargs['instance']:
            current_user = kwargs['instance'].user
            self.fields['reporting_manager'].queryset = User.objects.filter(
                is_active=True
            ).exclude(pk=current_user.pk)
        else:
            self.fields['reporting_manager'].queryset = User.objects.filter(is_active=True)


class EmployeeDocumentForm(forms.ModelForm):
    """Form for uploading employee documents"""
    
    class Meta:
        model = EmployeeDocument
        fields = ['document_type', 'title', 'description', 'file', 'expiry_date', 'notes']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_type'].label = 'Document Type'
        self.fields['title'].label = 'Document Title *'
        self.fields['description'].label = 'Description'
        self.fields['file'].label = 'Document File *'
        self.fields['expiry_date'].label = 'Expiry Date (if applicable)'
        self.fields['notes'].label = 'Additional Notes'


class EmployeeSkillForm(forms.ModelForm):
    """Form for adding employee skills"""
    
    class Meta:
        model = EmployeeSkill
        fields = ['skill_name', 'skill_level', 'years_of_experience', 'certification', 'certification_date', 'expiry_date', 'is_verified', 'notes']
        widgets = {
            'skill_name': forms.TextInput(attrs={'class': 'form-control'}),
            'skill_level': forms.Select(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'certification': forms.TextInput(attrs={'class': 'form-control'}),
            'certification_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['skill_name'].label = 'Skill Name *'
        self.fields['skill_level'].label = 'Skill Level *'
        self.fields['years_of_experience'].label = 'Years of Experience'
        self.fields['certification'].label = 'Certification (if any)'
        self.fields['certification_date'].label = 'Certification Date'
        self.fields['expiry_date'].label = 'Certification Expiry Date'
        self.fields['is_verified'].label = 'Verified'
        self.fields['notes'].label = 'Notes'


class CertificationForm(forms.ModelForm):
    """Form for managing professional certifications"""
    
    class Meta:
        model = Certification
        fields = ['certification_name', 'certification_number', 'issuing_organization', 'issue_date', 'expiry_date', 'certificate_file', 'is_active', 'notes']
        widgets = {
            'certification_name': forms.TextInput(attrs={'class': 'form-control'}),
            'certification_number': forms.TextInput(attrs={'class': 'form-control'}),
            'issuing_organization': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'certificate_file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['certification_name'].label = 'Certification Name *'
        self.fields['certification_number'].label = 'Certification Number'
        self.fields['issuing_organization'].label = 'Issuing Organization *'
        self.fields['issue_date'].label = 'Issue Date *'
        self.fields['expiry_date'].label = 'Expiry Date *'
        self.fields['certificate_file'].label = 'Certificate File'
        self.fields['is_active'].label = 'Active'
        self.fields['notes'].label = 'Notes'


class EmployeeAssetForm(forms.ModelForm):
    """Form for allocating assets to employees"""
    
    class Meta:
        model = EmployeeAsset
        fields = [
            'asset_type', 'asset_name', 'asset_tag', 'serial_number',
            'model', 'brand', 'allocation_date', 'return_date', 'condition', 'notes'
        ]
        widgets = {
            'asset_type': forms.Select(attrs={'class': 'form-control'}),
            'asset_name': forms.TextInput(attrs={'class': 'form-control'}),
            'asset_tag': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'allocation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset_type'].label = 'Asset Type *'
        self.fields['asset_name'].label = 'Asset Name *'
        self.fields['asset_tag'].label = 'Asset Tag *'
        self.fields['serial_number'].label = 'Serial Number'
        self.fields['model'].label = 'Model'
        self.fields['brand'].label = 'Brand'
        self.fields['allocation_date'].label = 'Allocation Date *'
        self.fields['return_date'].label = 'Return Date'
        self.fields['condition'].label = 'Condition'
        self.fields['notes'].label = 'Notes'


class DepartmentForm(forms.ModelForm):
    """Form for creating and editing departments"""
    
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'parent', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter manager to staff users only
        self.fields['manager'].queryset = User.objects.filter(is_staff=True, is_active=True)
        
        # Prevent circular reference in parent department
        if 'instance' in kwargs and kwargs['instance']:
            current_dept = kwargs['instance']
            self.fields['parent'].queryset = Department.objects.exclude(
                models.Q(pk=current_dept.pk) | 
                models.Q(parent__parent=current_dept) |
                models.Q(parent=current_dept)
            )
        else:
            self.fields['parent'].queryset = Department.objects.all()
        
        self.fields['name'].label = 'Department Name *'
        self.fields['code'].label = 'Department Code *'
        self.fields['description'].label = 'Description'
        self.fields['parent'].label = 'Parent Department'
        self.fields['manager'].label = 'Department Manager'
