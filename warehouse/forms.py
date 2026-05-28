from django import forms
from django.contrib.auth import get_user_model

from .models import Item, StockMovement, WarehouseRequest, WarehouseRequestItem, ItemSupplier, ItemAssignment, SerialNumber

User = get_user_model()


class StockMovementForm(forms.Form):
    item = forms.ModelChoiceField(queryset=Item.objects.none())
    movement_type = forms.ChoiceField(
        choices=[choice for choice in StockMovement.MOVEMENT_TYPES if choice[0] != "transfer"]
    )
    quantity = forms.IntegerField(min_value=0, help_text="For adjustment, enter the final counted stock.")
    reason = forms.CharField(max_length=200, required=False)
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = Item.objects.select_related("category").order_by("code", "name")
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["item"].widget.attrs["class"] = "form-select"
        self.fields["movement_type"].widget.attrs["class"] = "form-select"


class WarehouseRequestForm(forms.ModelForm):
    class Meta:
        model = WarehouseRequest
        fields = ["reason", "notes"]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ItemSupplierForm(forms.ModelForm):
    """Form for adding/editing suppliers for an item"""
    class Meta:
        model = ItemSupplier
        fields = ["supplier", "supplier_code", "description", "unit_price", "is_preferred", "lead_time_days", "min_order_quantity", "notes"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["supplier"].widget.attrs["class"] = "form-select"


class WarehouseRequestItemForm(forms.ModelForm):
    """Form for adding items to a warehouse request"""
    class Meta:
        model = WarehouseRequestItem
        fields = ["item", "quantity_requested", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = Item.objects.filter(status="active").order_by("code", "name")
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["item"].widget.attrs["class"] = "form-select"


class ItemAssignmentForm(forms.ModelForm):
    """Form for assigning items to users"""
    class Meta:
        model = ItemAssignment
        fields = ["user", "quantity_assigned", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.all().order_by('username')
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["user"].widget.attrs["class"] = "form-select"


class SerialNumberForm(forms.ModelForm):
    """Form for managing serial numbers"""
    class Meta:
        model = SerialNumber
        fields = ["serial_number", "status", "assigned_to", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.all().order_by('username')
        self.fields["assigned_to"].required = False
        self.fields["status"].required = False
        self.fields["serial_number"].required = False
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["status"].widget.attrs["class"] = "form-select"
        self.fields["assigned_to"].widget.attrs["class"] = "form-select"

    def clean_serial_number(self):
        """Validate serial number is unique per item"""
        serial_number = self.cleaned_data.get('serial_number')
        if serial_number:
            # Check if this serial number already exists for this item
            item = self.instance.item if hasattr(self, 'instance') and self.instance.item else None
            if item and self.instance.pk:
                # Editing existing serial number, check if another serial has the same number
                if SerialNumber.objects.filter(item=item, serial_number=serial_number).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('This serial number already exists for this item.')
            elif item:
                # Creating new serial number
                if SerialNumber.objects.filter(item=item, serial_number=serial_number).exists():
                    raise forms.ValidationError('This serial number already exists for this item.')
        return serial_number
