# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-19 07:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proceedings", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="proceedings",
            name="minimum_referees",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Require an explicit minimum number of referees for the default ref cycle.",
                null=True,
            ),
        ),
    ]
