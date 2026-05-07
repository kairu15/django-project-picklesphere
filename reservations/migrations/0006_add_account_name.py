# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0005_add_refund_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='cancellationrequest',
            name='account_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
