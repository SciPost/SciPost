# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-01 19:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("colleges", "0004_auto_20180629_0825"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prospectivefellowevent",
            name="noted_on",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
