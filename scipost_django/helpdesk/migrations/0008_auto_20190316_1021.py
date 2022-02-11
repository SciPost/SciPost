# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-16 09:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0007_auto_20190315_0551"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="queue",
            options={
                "ordering": ["name"],
                "permissions": [
                    ("can_manage_queue", "Can manage Queue"),
                    ("can_handle_queue", "Can handle Queue"),
                    ("can_view_queue", "Can view Queue"),
                ],
            },
        ),
        migrations.AlterField(
            model_name="ticket",
            name="status",
            field=models.CharField(
                choices=[
                    ("unassigned", "Unassigned, waiting for triage"),
                    ("assigned", "Assigned, waiting for handler"),
                    ("passedon", "Passed on to other handler"),
                    ("pickedup", "Picked up by handler"),
                    ("awaitingassignee", "Awaiting response from SciPost"),
                    ("awaitinguser", "Awaiting response from user"),
                    ("resolved", "Resolved"),
                    ("closed", "Closed"),
                ],
                max_length=32,
            ),
        ),
    ]
