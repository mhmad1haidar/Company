from django import forms

from .models import Car, FuelLog, MaintenanceHistory


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            "plate_number",
            "brand",
            "model",
            "year",
            "color",
            "fuel_type",
            "status",
            "assigned_employee",
            "insurance_expiry",
            "inspection_expiry",
            "registration_expiry",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Minimal Tailwind class injection for consistency.
        for field in self.fields.values():
            if hasattr(field.widget, "attrs"):
                cls = field.widget.attrs.get("class", "")
                # Add default classes without overriding custom ones.
                if "w-full" not in cls:
                    field.widget.attrs["class"] = (cls + " w-full border p-2 rounded").strip()


class MaintenanceHistoryForm(forms.ModelForm):
    class Meta:
        model = MaintenanceHistory
        fields = ["date", "type", "cost", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, "attrs"):
                cls = field.widget.attrs.get("class", "")
                if "w-full" not in cls:
                    field.widget.attrs["class"] = (cls + " w-full border p-2 rounded").strip()


class FuelLogForm(forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = ["date", "liters", "cost"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, "attrs"):
                cls = field.widget.attrs.get("class", "")
                if "w-full" not in cls:
                    field.widget.attrs["class"] = (cls + " w-full border p-2 rounded").strip()
