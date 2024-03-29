# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-19 21:24
from __future__ import unicode_literals

import comments.behaviors
from django.db import migrations, models
import scipost.storage


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0023_auto_20180519_1313"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="file_attachment",
            field=models.FileField(
                blank=True,
                storage=scipost.storage.SecureFileStorage(),
                upload_to="uploads/reports/%Y/%m/%d/",
                validators=[
                    comments.behaviors.validate_file_extension,
                    comments.behaviors.validate_max_file_size,
                ],
            ),
        ),
        migrations.AlterField(
            model_name="submission",
            name="status",
            field=models.CharField(
                choices=[
                    ("incoming", "Submission incoming, undergoing pre-screening"),
                    ("unassigned", "Unassigned, awaiting editor assignment"),
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
