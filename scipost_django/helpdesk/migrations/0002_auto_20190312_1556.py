# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-12 14:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("helpdesk", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="queue",
            options={
                "ordering": ["name"],
                "permissions": [("can_view_queue", "Can view Queue")],
            },
        ),
        migrations.AlterField(
            model_name="ticket",
            name="queue",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tickets",
                to="helpdesk.Queue",
            ),
        ),
    ]
