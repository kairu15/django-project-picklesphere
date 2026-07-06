from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import User
from courts.models import Court
from equipment.models import Equipment


class Reservation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name='reservations')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(0.5)])
    
    # Pricing
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    equipment_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    
    # Match settings
    match_name = models.CharField(max_length=100, blank=True, null=True)
    match_format = models.CharField(max_length=20, default='singles')
    game_type = models.CharField(max_length=20, default='friendly')
    scoring_format = models.CharField(max_length=20, default='11')
    points_per_game = models.IntegerField(default=11)
    games_to_win = models.IntegerField(default=2)
    win_by_two = models.BooleanField(default=True)

    # Staff approval
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reservations')
    approved_at = models.DateTimeField(null=True, blank=True)

    # Rating tracking
    is_rated = models.BooleanField(default=False, help_text='Whether this reservation has been rated by the user')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reservations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reservation #{self.id} - {self.user.username} - {self.court.name}"
    
    def calculate_total(self):
        hourly_rate = float(self.hourly_rate) if self.hourly_rate else 0.0
        duration_hours = float(self.duration_hours) if self.duration_hours else 0.0
        equipment_fee = float(self.equipment_fee) if self.equipment_fee else 0.0
        court_fee = hourly_rate * duration_hours
        return court_fee + equipment_fee
    
    def save(self, *args, **kwargs):
        # Calculate duration
        from datetime import datetime
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        duration = (end - start).total_seconds() / 3600
        self.duration_hours = round(duration, 1)
        
        # Calculate totals
        self.subtotal = float(self.hourly_rate) * float(self.duration_hours)
        self.total_amount = self.calculate_total()
        
        super().save(*args, **kwargs)


class ReservationEquipment(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='rented_equipment')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    rental_fee = models.DecimalField(max_digits=8, decimal_places=2)
    
    class Meta:
        db_table = 'reservation_equipment'
    
    def __str__(self):
        return f"{self.equipment.name} x{self.quantity} for Reservation #{self.reservation.id}"


class CancellationPolicy(models.Model):
    name = models.CharField(max_length=100, default='Default Cancellation Policy')
    time_limit_minutes = models.PositiveIntegerField(default=20, help_text='Time limit in minutes for cancellation after reservation creation')
    deduction_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=30, help_text='Percentage deduction for cancellation fee')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cancellation_policies'
        verbose_name_plural = 'Cancellation Policies'

    def __str__(self):
        return f"{self.name} ({self.deduction_percentage}% fee, {self.time_limit_minutes} min limit)"


class CancellationRequest(models.Model):
    REFUND_METHOD_CHOICES = (
        ('gcash', 'GCash'),
        ('paypal', 'PayPal'),
        ('card', 'Credit Card'),
    )

    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='cancellation_request')
    reason = models.TextField()
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_cancellations')
    approved_at = models.DateTimeField(null=True, blank=True)

    # Refund fields
    refund_method = models.CharField(max_length=20, choices=REFUND_METHOD_CHOICES, blank=True, null=True)
    gcash_number = models.CharField(max_length=20, blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)
    paypal_email = models.EmailField(blank=True, null=True)
    refund_processed = models.BooleanField(default=False)
    refund_processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds')

    # Cancellation policy fields
    deduction_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deduction_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    cancellation_note = models.TextField(blank=True, null=True)
    is_within_time_limit = models.BooleanField(default=True)

    class Meta:
        db_table = 'cancellation_requests'
        ordering = ['-requested_at']

    def __str__(self):
        return f"Cancellation Request for Reservation #{self.reservation.id}"


class ReservationInvitation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    )

    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'reservation_invitations'
        unique_together = [('reservation', 'invited_user')]

    def __str__(self):
        return f"Invitation for {self.invited_user.username} to Reservation #{self.reservation.id}"
