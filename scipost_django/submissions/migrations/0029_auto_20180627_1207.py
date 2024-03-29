# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-27 10:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0028_auto_20180621_0551"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="qualification",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (None, "-"),
                    (4, "expert in this subject"),
                    (3, "very knowledgeable in this subject"),
                    (2, "knowledgeable in this subject"),
                    (1, "generally qualified"),
                    (0, "not qualified"),
                ],
                null=True,
                verbose_name="Qualification to referee this: I am",
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="recommendation",
            field=models.SmallIntegerField(
                blank=True,
                choices=[
                    (None, "-"),
                    (
                        1,
                        "Publish as Tier I (top 10% of papers in this journal, qualifies as Select)",
                    ),
                    (2, "Publish as Tier II (top 50% of papers in this journal)"),
                    (3, "Publish as Tier III (meets the criteria of this journal)"),
                    (-1, "Ask for minor revision"),
                    (-2, "Ask for major revision"),
                    (-3, "Reject"),
                ],
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="report",
            field=models.TextField(blank=True),
        ),
    ]
