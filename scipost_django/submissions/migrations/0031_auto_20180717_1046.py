# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-17 08:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0030_merge_20180717_1041"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="invitation_order",
            field=models.IntegerField(default=0),
        ),
    ]
