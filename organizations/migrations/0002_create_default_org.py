from django.db import migrations
from django.utils.text import slugify


def create_default_organization(apps, schema_editor):
    """Create a default 'PickleSphere HQ' organization and assign all existing data to it."""
    Organization = apps.get_model('organizations', 'Organization')
    User = apps.get_model('accounts', 'User')
    Court = apps.get_model('courts', 'Court')
    Site = apps.get_model('courts', 'Site')
    Tournament = apps.get_model('tournaments', 'Tournament')
    Equipment = apps.get_model('equipment', 'Equipment')
    
    # Create default organization
    org, created = Organization.objects.get_or_create(
        name='PickleSphere HQ',
        defaults={
            'slug': 'picklesphere-hq',
            'description': 'The official PickleSphere headquarters organization.',
            'address': '123 Sports Avenue, Makati City',
            'city': 'Makati City',
            'province': 'Metro Manila',
            'contact_email': 'picklesphere@gmail.com',
            'contact_phone': '09455470173',
            'status': 'approved',
            'is_active': True,
        }
    )
    
    if created:
        print(f"Created default organization: {org.name}")
    else:
        print(f"Default organization already exists: {org.name}")
    
    # Migrate existing users with 'admin' role to 'super_admin'
    for user in User.objects.filter(role='admin'):
        user.role = 'super_admin'
        user.save(update_fields=['role'])
        print(f"Updated admin user {user.username} to super_admin")
    
    # Migrate existing users with 'staff' role to 'org_staff'
    for user in User.objects.filter(role='staff'):
        user.role = 'org_staff'
        user.organization = org
        user.save(update_fields=['role', 'organization'])
        print(f"Updated staff user {user.username} to org_staff")
    
    # Assign all existing sites to default organization
    for site in Site.objects.filter(organization__isnull=True):
        site.organization = org
        site.save(update_fields=['organization'])
    
    # Assign all existing courts to default organization
    for court in Court.objects.filter(organization__isnull=True):
        court.organization = org
        court.save(update_fields=['organization'])
    
    # Assign all existing tournaments to default organization
    for tournament in Tournament.objects.filter(organization__isnull=True):
        tournament.organization = org
        tournament.save(update_fields=['organization'])
    
    # Assign all existing equipment to default organization
    for equipment in Equipment.objects.filter(organization__isnull=True):
        equipment.organization = org
        equipment.save(update_fields=['organization'])


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        ('accounts', '0002_user_organization_alter_user_role'),
        ('courts', '0002_court_organization_site_organization'),
        ('tournaments', '0002_tournament_organization'),
        ('equipment', '0002_equipment_organization'),
    ]

    operations = [
        migrations.RunPython(create_default_organization),
    ]
