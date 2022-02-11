# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-13 10:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="report_type",
            field=models.CharField(
                choices=[
                    ("report_normal", "Normal Report"),
                    ("report_post_pub", "Post-publication Report"),
                ],
                default="report_normal",
                max_length=16,
            ),
        ),
    ]
