from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class EmployeeCreateForm(UserCreationForm):
    """Form for creating new employees"""
    
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
        self.fields['department'].label = 'Department'
        self.fields['job_title'].label = 'Job Title'
        self.fields['is_staff'].label = 'Staff Access (can manage employees)'
        self.fields['is_active'].label = 'Active Account'


class EmployeeEditForm(forms.ModelForm):
    """Form for editing existing employees"""
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'employee_id', 'department', 'job_title', 
            'is_staff', 'is_superuser', 'is_active'
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
        self.fields['department'].label = 'Department'
        self.fields['job_title'].label = 'Job Title'
        self.fields['is_staff'].label = 'Staff Access (can manage employees)'
        self.fields['is_superuser'].label = 'Superuser (full admin access)'
        self.fields['is_active'].label = 'Active Account'
