from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0002_create_default_org'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='operating_hours',
            field=models.TextField(blank=True, help_text='Operating hours description (e.g., Mon-Fri 6AM-10PM)', null=True),
        ),
    ]
