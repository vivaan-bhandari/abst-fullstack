# Generated by Django 4.2.23 on 2025-07-22 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residents", "0002_resident_deleted_at_resident_is_deleted"),
    ]

    operations = [
        migrations.AddField(
            model_name="resident",
            name="total_shift_times",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
