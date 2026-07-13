from django.db import models
from reservations.models import Reservation


class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    METHOD_CHOICES = (
        ('gcash', 'GCash'),
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
    )
    
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, blank=True, null=True)
    
    # For GCash payments (also used as generic proof of payment for any method)
    gcash_reference = models.CharField(max_length=100, blank=True, null=True)
    gcash_proof_image = models.ImageField(upload_to='payments/gcash/', blank=True, null=True)

    # For cash payments
    cash_received_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='cash_payments_received')
    cash_received_at = models.DateTimeField(null=True, blank=True)
    
    # Transaction details
    transaction_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    payment_notes = models.TextField(blank=True, null=True)

    # Stripe integration fields
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, db_index=True, help_text='Stripe PaymentIntent ID (pi_xxx)')
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True, db_index=True, help_text='Stripe Checkout Session ID (cs_xxx)')
    stripe_payment_method = models.CharField(max_length=50, blank=True, null=True, help_text='Stripe payment method type (card, gcash, grabpay, etc.)')
    stripe_receipt_url = models.URLField(max_length=500, blank=True, null=True, help_text='URL to the Stripe-hosted receipt')
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True, help_text='Stripe Charge ID (ch_xxx)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['reservation', 'status']),
            models.Index(fields=['method', 'status']),
        ]
    
    def __str__(self):
        return f"Payment #{self.id} - {self.reservation.user.username} - ₱{self.amount}"


class Refund(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    requested_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='refund_requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_refunds')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'refunds'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['payment', 'status']),
            models.Index(fields=['status', '-requested_at']),
        ]
    
    def __str__(self):
        return f"Refund #{self.id} - Payment #{self.payment.id} - ₱{self.amount}"


class PaymentLog(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment.id} - {self.action}"
