# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-13 19:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0032_merge_20180806_1236"),
    ]

    operations = [
        migrations.AlterField(
            model_name="editorialassignment",
            name="status",
            field=models.CharField(
                choices=[
                    ("preassigned", "Pre-assigned"),
                    ("invited", "Invited"),
                    ("accepted", "Accepted"),
                    ("declined", "Declined"),
                    ("completed", "Completed"),
                    ("deprecated", "Deprecated"),
                    ("replaced", "Replaced"),
                ],
                default="preassigned",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="submission",
            name="needs_conflicts_update",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="submission",
            name="status",
            field=models.CharField(
                choices=[
                    ("incoming", "Submission incoming, undergoing pre-screening"),
                    ("unassigned", "Unassigned, awaiting editor assignment"),
                    ("failed_pre", "Failed pre-screening"),
                    ("assigned", "Editor-in-charge assigned"),
                    (
                        "assignment_failed",
                        "Failed to assign Editor-in-charge; manuscript rejected",
                    ),
                    ("resubmitted", "Has been resubmitted"),
                    ("accepted", "Publication decision taken: accept"),
                    ("rejected", "Publication decision taken: reject"),
                    ("withdrawn", "Withdrawn by the Authors"),
                    ("published", "Published"),
                ],
                default="incoming",
                max_length=30,
            ),
        ),
    ]
