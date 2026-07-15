from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_fix_missing_broadcast_columns'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name='BroadcastMessage_target_users',
                ),
            ],
            database_operations=[],  # Keep the actual table intact
        ),
    ]
