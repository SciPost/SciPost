# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-02-24 05:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finances", "0013_subsidy_renewal_of"),
    ]

    operations = [
        migrations.AddField(
            model_name="subsidy",
            name="renewable",
            field=models.NullBooleanField(),
        ),
    ]
