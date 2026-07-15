"""
Migration: Fix missing broadcast_messages_target_users M2M through table.
The table was defined in 0001_initial.py but was never physically created in the database.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_emailotp'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BroadcastMessage_target_users',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('broadcastmessage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notifications.broadcastmessage')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'broadcast_messages_target_users',
                'unique_together': {('broadcastmessage', 'user')},
            },
        ),
    ]
