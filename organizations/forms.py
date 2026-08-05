from django import forms
from django.db.models import Q
from .models import Organization, OrganizationPaymentSettings
from accounts.models import User, StaffPermission
import re


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


class OrganizationPaymentSettingsForm(forms.ModelForm):
    """Form for Organization Admins to manage their own payment information."""

    class Meta:
        model = OrganizationPaymentSettings
        fields = [
            'gcash_number', 'gcash_account_name',
            'maya_number', 'maya_account_name',
            'bank_name', 'bank_account_name', 'bank_account_number',
            'qr_code', 'payment_instructions', 'accepted_payment_methods', 'is_active',
        ]
        widgets = {
            'gcash_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0917 123 4567'}),
            'gcash_account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name on GCash account'}),
            'maya_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0917 123 4567'}),
            'maya_account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name on Maya account'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BDO, BPI, UnionBank'}),
            'bank_account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name on bank account'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank account number'}),
            'qr_code': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'payment_instructions': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'e.g. 1) Send payment to the number above. 2) Take a screenshot of your reference number. 3) Upload it below to complete your booking.'
            }),
            'accepted_payment_methods': forms.CheckboxSelectMultiple(
                choices=OrganizationPaymentSettings.PAYMENT_METHOD_CHOICES,
                attrs={'class': 'form-check-input'}
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gcash_number'].required = False
        self.fields['gcash_account_name'].required = False
        self.fields['maya_number'].required = False
        self.fields['maya_account_name'].required = False
        self.fields['bank_name'].required = False
        self.fields['bank_account_name'].required = False
        self.fields['bank_account_number'].required = False
        self.fields['payment_instructions'].required = False
        self.fields['accepted_payment_methods'].required = False

    def clean_accepted_payment_methods(self):
        """Keep only valid method keys."""
        methods = self.cleaned_data.get('accepted_payment_methods') or []
        valid = dict(OrganizationPaymentSettings.PAYMENT_METHOD_CHOICES)
        return [m for m in methods if m in valid]

    def clean(self):
        cleaned_data = super().clean()
        methods = cleaned_data.get('accepted_payment_methods') or []
        errors = {}

        if 'gcash' in methods:
            if not cleaned_data.get('gcash_number'):
                errors['gcash_number'] = 'Provide a GCash number if GCash is an accepted method.'
            if not cleaned_data.get('gcash_account_name'):
                errors['gcash_account_name'] = 'Provide the GCash account name if GCash is an accepted method.'

        if 'maya' in methods:
            if not cleaned_data.get('maya_number'):
                errors['maya_number'] = 'Provide a Maya number if Maya is an accepted method.'
            if not cleaned_data.get('maya_account_name'):
                errors['maya_account_name'] = 'Provide the Maya account name if Maya is an accepted method.'

        if 'bank_transfer' in methods:
            for field in ('bank_name', 'bank_account_name', 'bank_account_number'):
                if not cleaned_data.get(field):
                    errors[field] = 'Complete the bank details if Bank Transfer is an accepted method.'

        for field, message in errors.items():
            self.add_error(field, message)

        return cleaned_data


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


class StaffAccountCreateForm(forms.ModelForm):
    """Form for org admin to create a new staff account from scratch."""
    
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )
    
    class Meta:
        model = User
        fields = [
            'first_name', 'middle_name', 'last_name', 'email', 'username',
            'phone_number', 'gender', 'birth_date',
            'department', 'employment_status', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Middle name (optional)'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09XXXXXXXXX'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Front Desk, Operations'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes about this staff member'}),
        }

    def __init__(self, *args, **kwargs):
        self.org = kwargs.pop('org', None)
        super().__init__(*args, **kwargs)
        self.fields['gender'].required = False
        self.fields['birth_date'].required = False
        self.fields['middle_name'].required = False
        self.fields['department'].required = False
        self.fields['employment_status'].required = False
        self.fields['notes'].required = False

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'org_staff'
        user.organization = self.org
        # Generate staff ID
        prefix = ''.join(re.findall(r'[A-Z]', self.org.name.upper()))[:3] if self.org else 'STF'
        if not prefix:
            prefix = 'STF'
        last_staff = User.objects.filter(
            staff_id__startswith=f'{prefix}-'
        ).order_by('-staff_id').first()
        if last_staff and last_staff.staff_id:
            last_num = int(last_staff.staff_id.split('-')[1])
            user.staff_id = f'{prefix}-{last_num + 1:04d}'
        else:
            user.staff_id = f'{prefix}-0001'
        if commit:
            user.save()
            # Create default permissions
            StaffPermission.objects.create(
                user=user,
            )
        return user


class StaffEditForm(forms.ModelForm):
    """Form for org admin to edit staff details."""
    class Meta:
        model = User
        fields = [
            'first_name', 'middle_name', 'last_name', 'email',
            'phone_number', 'gender', 'birth_date',
            'department', 'employment_status', 'notes', 'is_active'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09XXXXXXXXX'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gender'].required = False
        self.fields['birth_date'].required = False
        self.fields['middle_name'].required = False
        self.fields['department'].required = False
        self.fields['employment_status'].required = False
        self.fields['notes'].required = False
        self.fields['employment_status'].label = 'Employment Status'


class StaffPermissionForm(forms.ModelForm):
    """Form for org admin to configure staff permissions."""
    class Meta:
        model = StaffPermission
        fields = [
            'manage_reservations', 'manage_payments', 'manage_refunds',
            'manage_equipment', 'manage_tournaments', 'manage_notifications',
            'view_reports', 'manage_courts', 'manage_sites'
        ]
        widgets = {
            field: forms.CheckboxInput(attrs={'class': 'form-check-input'})
            for field in [
                'manage_reservations', 'manage_payments', 'manage_refunds',
                'manage_equipment', 'manage_tournaments', 'manage_notifications',
                'view_reports', 'manage_courts', 'manage_sites'
            ]
        }
        labels = {
            'manage_reservations': 'Can manage reservations',
            'manage_payments': 'Can manage payments',
            'manage_refunds': 'Can process refunds',
            'manage_equipment': 'Can manage equipment',
            'manage_tournaments': 'Can manage tournaments',
            'manage_notifications': 'Can send notifications',
            'view_reports': 'Can view reports',
            'manage_courts': 'Can manage courts',
            'manage_sites': 'Can manage sites',
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


class OrganizationVerificationForm(forms.ModelForm):
    """Form for super admin to toggle verification status."""
    class Meta:
        model = Organization
        fields = ['is_verified']
        widgets = {
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
        admin_qs = User.objects.filter(role='org_admin', is_active=True)
        if self.instance.pk:
            admin_qs = admin_qs.filter(
                Q(organization=self.instance) |
                Q(organization__isnull=True)
            ).distinct()
        else:
            admin_qs = admin_qs.filter(organization__isnull=True)
        self.fields['org_admin'].queryset = admin_qs.order_by('username')
        
        if self.instance.pk:
            current_admin = User.objects.filter(
                organization=self.instance, role='org_admin'
            ).first()
            if current_admin:
                self.fields['org_admin'].initial = current_admin.id
