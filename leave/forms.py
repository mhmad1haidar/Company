"""
Forms for the leave management system.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Leave, LeaveType


class LeaveRequestForm(forms.ModelForm):
    """
    Form for employees to request leave.
    """

    class Meta:
        model = Leave
        fields = ["leave_type", "start_date", "end_date", "reason", "attachment"]
        widgets = {
            "leave_type": forms.Select(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Provide a brief reason for your leave request..."
                }
            ),
            "attachment": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx,.jpg,.jpeg,.png"
                }
            ),
        }

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["leave_type"].queryset = LeaveType.objects.all()
        self.fields["leave_type"].empty_label = "Select leave type"
        
        # Set minimum date to today
        today = timezone.now().date()
        self.fields["start_date"].widget.attrs.update({"min": today})
        self.fields["end_date"].widget.attrs.update({"min": today})

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        leave_type = cleaned_data.get("leave_type")

        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError(
                    "End date must be on or after start date."
                )

            # Remove overlapping leave validation to allow multiple requests
            # Users can now submit multiple leave requests without restrictions

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance


class LeaveApprovalForm(forms.ModelForm):
    """
    Form for admins to approve or reject leave requests.
    """

    class Meta:
        model = Leave
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, user, *args, **kwargs):
        self.approver = user
        super().__init__(*args, **kwargs)
        # Only allow status changes to approved or rejected
        self.fields["status"].choices = [
            (Leave.Status.APPROVED, "Approve"),
            (Leave.Status.REJECTED, "Reject"),
        ]

    def clean_status(self):
        status = self.cleaned_data.get("status")
        if status == Leave.Status.PENDING:
            raise ValidationError("Status cannot be set back to pending.")
        return status

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.approved_by = self.approver
        instance.approved_at = timezone.now()
        if commit:
            instance.save()
        return instance


class LeaveFilterForm(forms.Form):
    """
    Form for filtering leave requests in the admin interface.
    """

    status = forms.ChoiceField(
        choices=[("", "All Status")] + list(Leave.Status.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    leave_type = forms.ModelChoiceField(
        queryset=LeaveType.objects.all(),
        empty_label="All Types",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    start_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    start_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    user = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search by username..."}
        ),
    )
