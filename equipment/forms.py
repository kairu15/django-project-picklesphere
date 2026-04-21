from django import forms
from .models import Equipment


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            'name',
            'type',
            'brand',
            'description',
            'quantity_total',
            'quantity_available',
            'rental_price',
            'purchase_price',
            'condition',
            'is_active',
            'image',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'quantity_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity_available': forms.NumberInput(attrs={'class': 'form-control'}),
            'rental_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        quantity_total = cleaned_data.get('quantity_total')
        quantity_available = cleaned_data.get('quantity_available')

        if quantity_total is not None and quantity_available is not None:
            if quantity_available > quantity_total:
                raise forms.ValidationError("Available quantity cannot exceed total quantity.")

        return cleaned_data
