# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-07 14:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finances", "0002_subsidy"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subsidy",
            name="amount",
            field=models.PositiveSmallIntegerField(help_text="in &euro; (rounded)"),
        ),
    ]
