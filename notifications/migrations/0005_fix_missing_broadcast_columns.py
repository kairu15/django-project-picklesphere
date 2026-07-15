"""
Migration: Add missing columns to broadcast_messages table.
Columns were defined in 0001_initial.py but never physically created.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_fix_missing_m2m_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='broadcastmessage',
            name='scheduled_for',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='broadcastmessage',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('sent', 'Sent'), ('scheduled', 'Scheduled')],
                default='draft',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='broadcastmessage',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('info', 'Info'), ('success', 'Success'),
                    ('warning', 'Warning'), ('error', 'Error'),
                ],
                default='info',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='broadcastmessage',
            name='category',
            field=models.CharField(
                choices=[
                    ('reservation', 'Reservations'), ('payment', 'Payments'),
                    ('refund', 'Refunds'), ('cancellation', 'Cancellations'),
                    ('tournament', 'Tournaments'), ('equipment', 'Equipment'),
                    ('organization', 'Organizations'), ('staff', 'Staff'),
                    ('user', 'Users'), ('report', 'Reports'),
                    ('system', 'System'), ('security', 'Security'),
                    ('maintenance', 'Maintenance'), ('announcement', 'Announcements'),
                    ('promotion', 'Promotions'), ('message', 'Messages'),
                    ('account', 'Account'),
                ],
                default='announcement',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='broadcastmessage',
            name='click_count',
            field=models.IntegerField(default=0),
        ),
    ]
