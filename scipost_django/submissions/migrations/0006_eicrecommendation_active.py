# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-23 22:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0005_auto_20180123_2312"),
    ]

    operations = [
        migrations.AddField(
            model_name="eicrecommendation",
            name="active",
            field=models.BooleanField(default=True),
        ),
    ]
