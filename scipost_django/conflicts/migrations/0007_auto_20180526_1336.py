# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-26 11:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("conflicts", "0006_auto_20180526_0923"),
    ]

    operations = [
        migrations.AlterField(
            model_name="conflictgroup",
            name="related_submissions",
            field=models.ManyToManyField(
                blank=True, related_name="conflict_groups", to="submissions.Submission"
            ),
        ),
    ]
