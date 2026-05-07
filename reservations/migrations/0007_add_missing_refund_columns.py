# Add missing refund columns manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0006_add_account_name'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE cancellation_requests 
                ADD COLUMN IF NOT EXISTS refund_processed TINYINT(1) DEFAULT 0,
                ADD COLUMN IF NOT EXISTS refund_processed_at DATETIME NULL,
                ADD COLUMN IF NOT EXISTS refund_method VARCHAR(20) NULL,
                ADD COLUMN IF NOT EXISTS gcash_number VARCHAR(20) NULL,
                ADD COLUMN IF NOT EXISTS account_name VARCHAR(100) NULL,
                ADD COLUMN IF NOT EXISTS paypal_email VARCHAR(254) NULL
            """,
            reverse_sql="""
                ALTER TABLE cancellation_requests 
                DROP COLUMN IF EXISTS refund_processed,
                DROP COLUMN IF EXISTS refund_processed_at,
                DROP COLUMN IF EXISTS refund_method,
                DROP COLUMN IF EXISTS gcash_number,
                DROP COLUMN IF EXISTS account_name,
                DROP COLUMN IF EXISTS paypal_email
            """
        ),
    ]
