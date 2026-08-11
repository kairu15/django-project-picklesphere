"""Rename the old system brand (PickleSphere) to 'Pickle Ball Reservation'.

Only touches system-owned branding/configuration rows (CMS settings and SMTP
sender name) that still contain the legacy name. User-created data
(organizations, reservations, messages, etc.) is left untouched.
"""

from django.db import migrations

OLD_BRAND = 'PickleSphere'
NEW_BRAND = 'Pickle Ball Reservation'
OLD_COPYRIGHT = '\u00a9 PickleSphere. All rights reserved.'
NEW_COPYRIGHT = '\u00a9 Pickle Ball Reservation. All rights reserved.'
OLD_HERO_TITLE = 'Welcome to PickleSphere'
NEW_HERO_TITLE = 'Welcome to Pickle Ball Reservation'


def update_branding(apps, schema_editor):
    SiteBranding = apps.get_model('dashboard', 'SiteBranding')
    NavBarSettings = apps.get_model('dashboard', 'NavBarSettings')
    FooterSettings = apps.get_model('dashboard', 'FooterSettings')
    SiteSettings = apps.get_model('dashboard', 'SiteSettings')
    HeroSectionSettings = apps.get_model('dashboard', 'HeroSectionSettings')
    SmtpConfiguration = apps.get_model('notifications', 'SmtpConfiguration')

    SiteBranding.objects.filter(brand_name=OLD_BRAND).update(brand_name=NEW_BRAND)
    NavBarSettings.objects.filter(brand_text=OLD_BRAND).update(brand_text=NEW_BRAND)
    FooterSettings.objects.filter(organization_name=OLD_BRAND).update(organization_name=NEW_BRAND)
    FooterSettings.objects.filter(copyright_text=OLD_COPYRIGHT).update(copyright_text=NEW_COPYRIGHT)
    SiteSettings.objects.filter(copyright_text=OLD_COPYRIGHT).update(copyright_text=NEW_COPYRIGHT)
    HeroSectionSettings.objects.filter(title=OLD_HERO_TITLE).update(title=NEW_HERO_TITLE)
    SmtpConfiguration.objects.filter(sender_name=OLD_BRAND).update(sender_name=NEW_BRAND)


def reverse_branding(apps, schema_editor):
    SiteBranding = apps.get_model('dashboard', 'SiteBranding')
    NavBarSettings = apps.get_model('dashboard', 'NavBarSettings')
    FooterSettings = apps.get_model('dashboard', 'FooterSettings')
    SiteSettings = apps.get_model('dashboard', 'SiteSettings')
    HeroSectionSettings = apps.get_model('dashboard', 'HeroSectionSettings')
    SmtpConfiguration = apps.get_model('notifications', 'SmtpConfiguration')

    SiteBranding.objects.filter(brand_name=NEW_BRAND).update(brand_name=OLD_BRAND)
    NavBarSettings.objects.filter(brand_text=NEW_BRAND).update(brand_text=OLD_BRAND)
    FooterSettings.objects.filter(organization_name=NEW_BRAND).update(organization_name=OLD_BRAND)
    FooterSettings.objects.filter(copyright_text=NEW_COPYRIGHT).update(copyright_text=OLD_COPYRIGHT)
    SiteSettings.objects.filter(copyright_text=NEW_COPYRIGHT).update(copyright_text=OLD_COPYRIGHT)
    HeroSectionSettings.objects.filter(title=NEW_HERO_TITLE).update(title=OLD_HERO_TITLE)
    SmtpConfiguration.objects.filter(sender_name=NEW_BRAND).update(sender_name=OLD_BRAND)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_add_website_design_cms_models'),
        ('notifications', '0006_remove_phantom_m2m_model'),
    ]

    operations = [
        migrations.RunPython(update_branding, reverse_branding),
    ]
