# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-08 14:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finances", "0005_auto_20181008_1405"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subsidy",
            name="amount",
            field=models.PositiveIntegerField(help_text="in &euro; (rounded)"),
        ),
    ]
