from django.db import models
from accounts.models import User


class Equipment(models.Model):
    TYPE_CHOICES = (
        ('paddle', 'Paddle'),
        ('ball', 'Ball'),
        ('net', 'Net'),
        ('shoes', 'Shoes'),
        ('other', 'Other'),
    )
    
    CONDITION_CHOICES = (
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    )
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Inventory
    quantity_total = models.PositiveIntegerField(default=1)
    quantity_available = models.PositiveIntegerField(default=1)
    quantity_reserved = models.PositiveIntegerField(default=0)
    
    # Pricing
    rental_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    purchase_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    
    # Status
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    is_active = models.BooleanField(default=True)
    
    # Images
    image = models.ImageField(upload_to='equipment/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'equipment'
        ordering = ['type', 'name']
        verbose_name_plural = 'Equipment'
    
    def __str__(self):
        return f"{self.name} ({self.type}) - Qty: {self.quantity_available}"
    
    def is_in_stock(self):
        return self.quantity_available > 0


class EquipmentRental(models.Model):
    STATUS_CHOICES = (
        ('reserved', 'Reserved'),
        ('rented', 'Rented'),
        ('returned', 'Returned'),
        ('damaged', 'Damaged/Lost'),
    )
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='rentals')
    rented_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipment_rentals')
    reserved_date = models.DateField()
    
    # Rental period
    rented_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reserved')
    rental_fee = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Condition check
    condition_out = models.CharField(max_length=20, choices=Equipment.CONDITION_CHOICES, blank=True, null=True)
    condition_in = models.CharField(max_length=20, choices=Equipment.CONDITION_CHOICES, blank=True, null=True)
    
    # Staff
    checked_out_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checkouts')
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checkins')
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'equipment_rentals'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.equipment.name} rented by {self.rented_by.username}"


class EquipmentMaintenance(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_date = models.DateField()
    description = models.TextField()
    performed_by = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    next_maintenance_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'equipment_maintenance'
        ordering = ['-maintenance_date']
    
    def __str__(self):
        return f"Maintenance for {self.equipment.name} on {self.maintenance_date}"
