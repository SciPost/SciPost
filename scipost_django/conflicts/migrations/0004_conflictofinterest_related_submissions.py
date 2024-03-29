# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-25 13:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0026_submission_needs_conflicts_update"),
        ("conflicts", "0003_auto_20180525_1438"),
    ]

    operations = [
        migrations.AddField(
            model_name="conflictofinterest",
            name="related_submissions",
            field=models.ManyToManyField(
                blank=True, related_name="conflicts", to="submissions.Submission"
            ),
        ),
    ]
