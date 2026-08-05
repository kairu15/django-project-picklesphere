"""
Migration: Add missing columns to broadcast_messages table.
Columns were defined in 0001_initial.py but never physically created at the
time this fix was written.

The current 0001_initial.py fully defines these columns, so this migration is
only kept for databases that were migrated before the fix and must not attempt
to re-add the columns on fresh databases.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_fix_missing_m2m_table'),
    ]

    operations = []
