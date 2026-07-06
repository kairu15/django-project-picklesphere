from django import forms
from django.db.models import Q
from .models import Organization
from accounts.models import User


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


class OrgStaffAssignmentForm(forms.Form):
    """Form for org admin to assign a user as staff member."""
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=True,
        label='Select User',
        widget=forms.Select(attrs={'class': 'form-select', 'style': 'border-radius: 10px;'})
    )
    
    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org', None)
        super().__init__(*args, **kwargs)
        if org:
            # Show users who are NOT already staff/admin of this org, and not super_admin
            existing_staff = User.objects.filter(
                organization=org,
                role__in=['org_admin', 'org_staff']
            ).values_list('id', flat=True)
            self.fields['user'].queryset = User.objects.filter(
                role='user',
                is_active=True
            ).exclude(id__in=existing_staff).order_by('username')
            if not self.fields['user'].queryset.exists():
                self.fields['user'].empty_label = "No eligible users available"
    
    
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


class SuperAdminOrganizationForm(forms.ModelForm):
    """Full organization management form for Super Admin"""
    
    org_admin = forms.ModelChoiceField(
        queryset=User.objects.filter(role='org_admin', is_active=True).order_by('username'),
        required=False,
        label='Organization Administrator',
        widget=forms.Select(attrs={'class': 'form-select select2-enhanced'})
    )
    
    class Meta:
        model = Organization
        fields = [
            'name', 'description', 'address', 'city', 'province',
            'contact_email', 'contact_phone', 'website',
            'logo', 'banner', 'operating_hours',
            'status', 'is_active', 'max_staff_accounts',
            'registration_notes', 'rejection_reason',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the organization'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province/State'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@organization.com'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact phone number'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://website.com'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'banner': forms.FileInput(attrs={'class': 'form-control'}),
            'operating_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g. Mon-Fri: 6:00 AM - 10:00 PM\nSat: 6:00 AM - 10:00 PM\nSun: 7:00 AM - 9:00 PM'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_staff_accounts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'registration_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Registration notes'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason for rejection'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter org_admin dropdown to only unassigned users (or the current assigned one)
        admin_qs = User.objects.filter(role='org_admin', is_active=True)
        if self.instance.pk:
            # When editing, include the currently assigned admin
            admin_qs = admin_qs.filter(
                Q(organization=self.instance) |
                Q(organization__isnull=True)
            ).distinct()
        else:
            admin_qs = admin_qs.filter(organization__isnull=True)
        self.fields['org_admin'].queryset = admin_qs.order_by('username')
        
        # Set initial value if editing
        if self.instance.pk:
            current_admin = User.objects.filter(
                organization=self.instance, role='org_admin'
            ).first()
            if current_admin:
                self.fields['org_admin'].initial = current_admin.id
