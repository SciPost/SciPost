# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-26 11:36
from __future__ import unicode_literals

from django.db import migrations


def rename_assignment_statuses(apps, schema_editor):
    """Rename EditorialAssignment incoming status."""
    EditorialAssignment = apps.get_model("submissions", "EditorialAssignment")

    # Update statuses
    EditorialAssignment.objects.filter(deprecated=True).update(status="deprecated")
    EditorialAssignment.objects.filter(deprecated=False, accepted__isnull=True).update(
        status="invited"
    )
    EditorialAssignment.objects.filter(deprecated=False, accepted=False).update(
        status="declined"
    )
    EditorialAssignment.objects.filter(
        deprecated=False, accepted=True, completed=False
    ).update(status="accepted")
    EditorialAssignment.objects.filter(
        deprecated=False, accepted=True, completed=True
    ).update(status="completed")


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0027_auto_20180526_1336"),
    ]

    operations = [
        migrations.RunPython(rename_assignment_statuses),
    ]
