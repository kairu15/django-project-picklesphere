from django import forms
from .models import Court, Site


class CourtForm(forms.ModelForm):
    amenities_text = forms.CharField(
        required=False,
        label='Amenities',
        help_text='Separate amenities with commas (e.g. Lights, Seating, Shower).',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lights, Seating, Shower'})
    )

    class Meta:
        model = Court
        fields = [
            'name',
            'site',
            'court_type',
            'status',
            'hourly_rate',
            'description',
            'image',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'site': forms.Select(attrs={'class': 'form-select'}),
            'court_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter sites to only show active ones from database
        self.fields['site'].queryset = Site.objects.filter(is_active=True).order_by('name')
        if self.instance and self.instance.pk and self.instance.amenities:
            self.fields['amenities_text'].initial = ', '.join(self.instance.amenities)

    def clean_amenities_text(self):
        amenities_text = self.cleaned_data.get('amenities_text', '')
        return [item.strip() for item in amenities_text.split(',') if item.strip()]

    def save(self, commit=True):
        court = super().save(commit=False)
        court.amenities = self.cleaned_data.get('amenities_text', [])
        if commit:
            court.save()
        return court
