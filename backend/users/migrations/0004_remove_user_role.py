# Generated manually to fix role constraint issue

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_userprofile'),
    ]

    operations = [
        migrations.RunSQL(
            # Remove the role column from auth_user table
            "ALTER TABLE auth_user DROP COLUMN role;",
            # Reverse operation (add it back if needed)
            "ALTER TABLE auth_user ADD COLUMN role varchar(20) NOT NULL DEFAULT 'staff';"
        ),
    ]
