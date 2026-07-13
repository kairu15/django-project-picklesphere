"""
Data migration: Seed default SocialPlatformSettings entries.

Creates the 7 core social media platforms with sensible defaults
so they appear in the CMS without requiring admin to click "Init Defaults".
"""

from django.db import migrations


DEFAULT_PLATFORMS = [
    {
        'platform': 'facebook',
        'is_active': True,
        'show_in_topbar': True,
        'show_in_footer': True,
        'open_in_new_tab': True,
        'display_order': 1,
    },
    {
        'platform': 'twitter',
        'is_active': True,
        'show_in_topbar': True,
        'show_in_footer': True,
        'open_in_new_tab': True,
        'display_order': 2,
    },
    {
        'platform': 'instagram',
        'is_active': True,
        'show_in_topbar': True,
        'show_in_footer': True,
        'open_in_new_tab': True,
        'display_order': 3,
    },
    {
        'platform': 'linkedin',
        'is_active': True,
        'show_in_topbar': False,
        'show_in_footer': True,
        'open_in_new_tab': True,
        'display_order': 4,
    },
    {
        'platform': 'youtube',
        'is_active': True,
        'show_in_topbar': False,
        'show_in_footer': True,
        'open_in_new_tab': True,
        'display_order': 5,
    },
    {
        'platform': 'tiktok',
        'is_active': True,
        'show_in_topbar': False,
        'show_in_footer': True,
        'open_in_new_tab': True,
        'display_order': 6,
    },
    {
        'platform': 'whatsapp',
        'is_active': True,
        'show_in_topbar': False,
        'show_in_footer': True,
        'open_in_new_tab': True,
        'display_order': 7,
    },
]


def seed_social_platforms(apps, schema_editor):
    """Create default social platform entries if they don't exist."""
    SocialPlatformSettings = apps.get_model('dashboard', 'SocialPlatformSettings')
    for data in DEFAULT_PLATFORMS:
        SocialPlatformSettings.objects.get_or_create(
            platform=data['platform'],
            defaults=data,
        )


def reverse_seed(apps, schema_editor):
    """Remove seeded platforms (only those with no URL set)."""
    SocialPlatformSettings = apps.get_model('dashboard', 'SocialPlatformSettings')
    platforms = [p['platform'] for p in DEFAULT_PLATFORMS]
    SocialPlatformSettings.objects.filter(
        platform__in=platforms,
        url='',
    ).delete()


class Migration(migrations.Migration):
    """Seed default social media platforms."""

    dependencies = [
        ('dashboard', '0004_footerquicklink_footersettings_herosectionsettings_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_social_platforms, reverse_seed),
    ]
