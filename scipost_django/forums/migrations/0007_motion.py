# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-09 17:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("forums", "0006_meeting"),
    ]

    operations = [
        migrations.CreateModel(
            name="Motion",
            fields=[
                (
                    "post_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="forums.Post",
                    ),
                ),
                ("voting_deadline", models.DateField()),
                ("accepted", models.NullBooleanField()),
                (
                    "eligible_for_voting",
                    models.ManyToManyField(
                        blank=True,
                        related_name="eligible_to_vote_on_motion",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "in_abstain",
                    models.ManyToManyField(
                        blank=True,
                        related_name="abstain_with_motion",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "in_agreement",
                    models.ManyToManyField(
                        blank=True,
                        related_name="agree_on_motion",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "in_disagreement",
                    models.ManyToManyField(
                        blank=True,
                        related_name="disagree_with_motion",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "in_doubt",
                    models.ManyToManyField(
                        blank=True,
                        related_name="doubt_on_motion",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            bases=("forums.post",),
        ),
    ]
