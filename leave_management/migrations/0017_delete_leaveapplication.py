# Generated by Django 4.2.16 on 2025-04-30 18:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leave_management', '0016_rename_seen_notification_is_read'),
    ]

    operations = [
        migrations.DeleteModel(
            name='LeaveApplication',
        ),
    ]
