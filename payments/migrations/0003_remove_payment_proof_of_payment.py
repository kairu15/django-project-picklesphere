# Generated manually to remove proof_of_payment field

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0002_payment_proof_of_payment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='proof_of_payment',
        ),
    ]
