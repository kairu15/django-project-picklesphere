from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('org_admin', 'Organization Admin'),
        ('org_staff', 'Organization Staff'),
        ('user', 'User'),
    )
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Organization association (for org_admin and org_staff)
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='members'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    def is_org_admin(self):
        return self.role == 'org_admin'
    
    def is_org_staff(self):
        return self.role == 'org_staff'
    
    def is_normal_user(self):
        return self.role == 'user'
    
    def is_admin(self):
        """Legacy - checks if user is super_admin or org_admin"""
        return self.role in ['super_admin', 'org_admin']
    
    def is_staff_user(self):
        """Legacy - checks if user has staff-level access"""
        return self.role in ['super_admin', 'org_admin', 'org_staff']


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.action}"
