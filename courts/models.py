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

    def get_time_slots(self, date):
        """
        Get 1-hour time slots from 8:00 AM to 11:00 PM for a specific date.
        Returns list of dicts with start_time, end_time, and available status.
        """
        from reservations.models import Reservation
        from datetime import time, datetime, timedelta

        slots = []
        start_hour = 8
        end_hour = 23

        # Get existing reservations for this court and date
        existing_reservations = Reservation.objects.filter(
            court=self,
            date=date,
            status__in=['confirmed', 'pending']
        )

        for hour in range(start_hour, end_hour + 1):
            slot_start = time(hour, 0)
            slot_end = time(hour + 1, 0) if hour < 23 else time(23, 59)

            # Check if slot overlaps with any existing reservation
            is_available = True
            for res in existing_reservations:
                res_start = res.start_time
                res_end = res.end_time

                # Slot is occupied if it overlaps with reservation
                # Overlap occurs when: slot_start < res_end AND slot_end > res_start
                if slot_start < res_end and slot_end > res_start:
                    is_available = False
                    break

            slots.append({
                'start': slot_start.strftime('%H:%M'),
                'end': slot_end.strftime('%H:%M'),
                'start_time': slot_start,
                'end_time': slot_end,
                'available': is_available,
                'label': f"{slot_start.strftime('%I:%M %p')} – {slot_end.strftime('%I:%M %p')}"
            })

        return slots


class CourtImage(models.Model):
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='courts/gallery/')
    alt_text = models.CharField(max_length=200, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'court_images'
        ordering = ['order', '-is_primary', '-created_at']

    def __str__(self):
        return f"{self.court.name} - Image {self.id}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per court
        if self.is_primary:
            CourtImage.objects.filter(court=self.court, is_primary=True).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


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
