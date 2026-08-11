from django import forms
from .models import Payment, Refund


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['method']
        widgets = {
            'method': forms.RadioSelect(choices=Payment.METHOD_CHOICES),
        }


class GCashPaymentForm(forms.ModelForm):
    # Reference & proof are required for online payments (matching the checkout UI).
    # Without this, an empty submission can create a pending payment with no way to
    # display a reference number on the payment status page.
    gcash_reference = forms.CharField(
        required=True,
        max_length=100,
        strip=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Reference Number'
        }),
        error_messages={'required': 'Please enter your payment reference number.'},
    )
    gcash_proof_image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        error_messages={'required': 'Please upload your proof of payment.'},
    )

    class Meta:
        model = Payment
        fields = ['gcash_reference', 'gcash_proof_image']


class CashPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_notes', 'gcash_proof_image']
        widgets = {
            'payment_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
            'gcash_proof_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }


class PaymentApprovalForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['status', 'payment_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class RefundRequestForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ['amount', 'reason']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please provide a reason for the refund request...'
            }),
        }
