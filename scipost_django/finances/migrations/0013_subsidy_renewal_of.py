# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-02-23 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finances", "0012_subsidyattachment"),
    ]

    operations = [
        migrations.AddField(
            model_name="subsidy",
            name="renewal_of",
            field=models.ManyToManyField(
                blank=True, related_name="renewed_by", to="finances.Subsidy"
            ),
        ),
    ]
