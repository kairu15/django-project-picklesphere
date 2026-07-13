""""
Data migration: Seed default singleton CMS settings.

Creates the singleton rows (pk=1) for HeroSectionSettings, SiteBranding,
TopBarSettings, NavBarSettings, and FooterSettings so they auto-populate
on first deploy — no "Init Defaults" button needed.
"""""

from django.db import migrations


MODELS = [
    'HeroSectionSettings',
    'SiteBranding',
    'TopBarSettings',
    'NavBarSettings',
    'FooterSettings',
]


def seed_cms_settings(apps, schema_editor):
    """Create singleton rows for all 5 CMS settings models if they don't exist."""
    for model_name in MODELS:
        Model = apps.get_model('dashboard', model_name)
        Model.objects.get_or_create(pk=1)


def reverse_seed(apps, schema_editor):
    """Remove the singleton rows (only pk=1)."""
    for model_name in MODELS:
        Model = apps.get_model('dashboard', model_name)
        Model.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    """Seed default CMS singleton settings."""

    dependencies = [
        ('dashboard', '0005_seed_social_platforms'),
    ]

    operations = [
        migrations.RunPython(seed_cms_settings, reverse_seed),
    ]
