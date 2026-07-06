from django import forms
from .models import Organization


class OrganizationRegistrationForm(forms.ModelForm):
    """Form for organizations to register on the platform"""
    
    agree_terms = forms.BooleanField(required=True, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))
    
    class Meta:
        model = Organization
        fields = ['name', 'description', 'address', 'city', 'province', 
                  'contact_email', 'contact_phone', 'website', 'registration_notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Organization Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about your pickleball organization'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province/State'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@organization.com'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact phone number'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourwebsite.com'}),
            'registration_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Why do you want to join PickleSphere? Any additional information?'}),
        }
        labels = {
            'registration_notes': 'Why Join PickleSphere?',
        }


class OrganizationProfileForm(forms.ModelForm):
    """Form for organization admins to update their profile"""
    
    class Meta:
        model = Organization
        fields = ['name', 'description', 'logo', 'banner', 'address', 'city', 'province',
                  'contact_email', 'contact_phone', 'website']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'banner': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }


class OrganizationApprovalForm(forms.ModelForm):
    """Form for super admin to approve/reject organizations"""
    
    class Meta:
        model = Organization
        fields = ['status', 'rejection_reason', 'max_staff_accounts']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for rejection (if applicable)'}),
            'max_staff_accounts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 50}),
        }
