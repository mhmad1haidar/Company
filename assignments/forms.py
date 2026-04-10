from django import forms
from django.db import models
from .models import WorkAssignment
from interventions.models import Intervention
from django.contrib.auth import get_user_model

User = get_user_model()


class WorkAssignmentForm(forms.ModelForm):
    """Form for creating and editing work assignments"""
    
    # Custom field for manual code entry
    codice_nigit_input = forms.CharField(
        label='Intervention Code (Codice NIGIT) *',
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Codice NIGIT (e.g., N0260001)'
        }),
        help_text='Enter the intervention code to assign'
    )
    
    class Meta:
        model = WorkAssignment
        fields = [
            'assigned_to',
            'vehicle',
            'assignment_note',
            'status',
            'scheduled_date'
        ]
        widgets = {
            'assigned_to': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5'
            }),
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'assignment_note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter specific instructions for the employee...'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set queryset for assigned_to to include all active users
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        # Pre-fill codice_nigit_input if editing existing assignment
        if self.instance and self.instance.pk and hasattr(self.instance, 'intervention') and self.instance.intervention:
            self.fields['codice_nigit_input'].initial = self.instance.intervention.codice_nigit
        
        # Add custom labels
        self.fields['assigned_to'].label = 'Assign To Employee(s) *'
        self.fields['assigned_to'].help_text = 'Hold Ctrl/Cmd to select multiple employees'
        self.fields['vehicle'].label = 'Vehicle (Optional)'
        self.fields['assignment_note'].label = 'Assignment Instructions *'
        self.fields['status'].label = 'Status'
        self.fields['scheduled_date'].label = 'Scheduled Date (Optional)'
    
    def clean_codice_nigit_input(self):
        """Validate and look up intervention by code"""
        codice_nigit = self.cleaned_data.get('codice_nigit_input')
        if not codice_nigit:
            raise forms.ValidationError('Please enter an intervention code.')
        
        # Look up intervention by code
        try:
            intervention = Intervention.objects.get(codice_nigit__iexact=codice_nigit.strip())
            return intervention
        except Intervention.DoesNotExist:
            raise forms.ValidationError(f'No intervention found with code "{codice_nigit}". Please check the code and try again.')
    
    def clean_assigned_to(self):
        """Validate at least one employee is selected"""
        assigned_to = self.cleaned_data.get('assigned_to')
        if not assigned_to or len(assigned_to) == 0:
            raise forms.ValidationError('Please select at least one employee to assign the work to.')
        return assigned_to
    
    def clean_assignment_note(self):
        """Validate assignment note"""
        assignment_note = self.cleaned_data.get('assignment_note')
        if not assignment_note or assignment_note.strip() == '':
            raise forms.ValidationError('Please provide assignment instructions.')
        return assignment_note
    
    def clean(self):
        cleaned_data = super().clean()
        # Set the intervention from the validated code
        if 'codice_nigit_input' in self.cleaned_data:
            cleaned_data['intervention'] = self.cleaned_data['codice_nigit_input']
        return cleaned_data
    
    def save(self, commit=True):
        # Get the intervention from cleaned_data
        intervention = self.cleaned_data.get('intervention')
        
        # Create the instance without saving
        instance = super().save(commit=False)
        
        # Set the intervention
        instance.intervention = intervention
        
        if commit:
            instance.save()
            # Save many-to-many relationships
            self.save_m2m()
        
        return instance


class WorkAssignmentStatusForm(forms.ModelForm):
    """Simple form for updating assignment status"""
    
    class Meta:
        model = WorkAssignment
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
