# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-25 12:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0025_auto_20180520_1430"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="needs_conflicts_update",
            field=models.BooleanField(default=True),
        ),
    ]
