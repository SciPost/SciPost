# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-16 14:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import scipost.models


class Migration(migrations.Migration):
    dependencies = [
        ("scipost", "0014_auto_20180414_2218"),
        ("profiles", "0002_auto_20180916_1643"),
        ("colleges", "0006_auto_20180703_1208"),
    ]

    operations = [
        migrations.CreateModel(
            name="PotentialFellowship",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("identified", "Identified as potential Fellow"),
                            ("invited", "Invited to become Fellow"),
                            ("reinvited", "Reinvited after initial invitation"),
                            ("multiplyreinvited", "Multiply reinvited"),
                            ("declined", "Declined the invitation"),
                            ("unresponsive", "Marked as unresponsive"),
                            ("retired", "Retired"),
                            ("deceased", "Deceased"),
                            (
                                "interested",
                                "Marked as interested, Fellowship being set up",
                            ),
                            ("registered", "Registered as Contributor"),
                            ("activeincollege", "Currently active in a College"),
                            ("emeritus", "SciPost Emeritus"),
                        ],
                        default="identified",
                        max_length=32,
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="profiles.Profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PotentialFellowshipEvent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "event",
                    models.CharField(
                        choices=[
                            ("defined", "Defined in database"),
                            ("emailed", "Emailed with invitation"),
                            ("responded", "Response received"),
                            ("statusupdated", "Status updated"),
                            ("comment", "Comment"),
                            ("deactivation", "Deactivation: not considered anymore"),
                        ],
                        max_length=32,
                    ),
                ),
                ("comments", models.TextField(blank=True)),
                ("noted_on", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "noted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET(scipost.models.get_sentinel_user),
                        to="scipost.Contributor",
                    ),
                ),
                (
                    "potfel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="colleges.PotentialFellowship",
                    ),
                ),
            ],
        ),
    ]
