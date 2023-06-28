# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-18 12:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0008_auto_20180127_2208"),
        ("journals", "0013_auto_20180216_0850"),
        ("scipost", "0004_auto_20180212_1932"),
        ("invitations", "0007_auto_20180218_1200"),
    ]

    operations = [
        migrations.CreateModel(
            name="CitationNotification",
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
                ("processed", models.BooleanField(default=False)),
                (
                    "cited_in_publication",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="journals.Publication",
                    ),
                ),
                (
                    "cited_in_submission",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="submissions.Submission",
                    ),
                ),
                (
                    "contributor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="scipost.Contributor",
                    ),
                ),
            ],
            options={
                "default_related_name": "citation_notifications",
            },
        ),
        migrations.RemoveField(
            model_name="registrationinvitation",
            name="cited_in_publications",
        ),
        migrations.RemoveField(
            model_name="registrationinvitation",
            name="cited_in_submissions",
        ),
        migrations.AddField(
            model_name="citationnotification",
            name="invitation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="citation_notifications",
                to="invitations.RegistrationInvitation",
            ),
        ),
    ]
