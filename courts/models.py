from django.db import models


class Site(models.Model):
    name = models.CharField(max_length=100)  # e.g. 1st Floor, Outdoor
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sites'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Court(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('maintenance', 'Under Maintenance'),
        ('reserved', 'Reserved'),
    )
    
    COURT_TYPE_CHOICES = (
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
    )
    
    name = models.CharField(max_length=100)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='courts')
    court_type = models.CharField(max_length=20, choices=COURT_TYPE_CHOICES, default='indoor')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    description = models.TextField(blank=True, null=True)
    amenities = models.JSONField(default=list, blank=True)
    image = models.ImageField(upload_to='courts/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courts'
        ordering = ['site', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.site.name})"
    
    def is_available(self, date, start_time, end_time):
        from reservations.models import Reservation
        overlapping = Reservation.objects.filter(
            court=self,
            date=date,
            status__in=['confirmed', 'pending']
        ).exclude(
            start_time__gte=end_time
        ).exclude(
            end_time__lte=start_time
        )
        return not overlapping.exists()


class CourtAvailability(models.Model):
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.IntegerField(choices=[(i, i) for i in range(7)])  # 0=Monday
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'court_availability'
        unique_together = ['court', 'day_of_week']
    
    def __str__(self):
        return f"{self.court.name} - Day {self.day_of_week}"
