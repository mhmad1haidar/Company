"""
Forms for attendance management
"""
from django import forms
from django.contrib.auth import get_user_model
from .models import Attendance

User = get_user_model()


class ManualAttendanceForm(forms.ModelForm):
    """Form for manual attendance entry."""
    
    class Meta:
        model = Attendance
        fields = ['user', 'date', 'check_in', 'check_out', 'break_duration', 'standard_hours', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_in': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'check_out': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'break_duration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
            'standard_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['user'].widget.attrs.update({'class': 'form-control'})
