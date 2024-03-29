# Generated by Django 3.2.16 on 2023-01-19 14:06

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("scipost", "0040_auto_20210310_2026"),
        ("profiles", "0035_alter_profile_title"),
        ("submissions", "0137_alter_qualification_expertise_level"),
        ("ethics", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubmissionClearance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "asserted_on",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("comments", models.TextField(blank=True)),
                (
                    "asserted_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="asserted_submission_clearances",
                        to="scipost.contributor",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submission_clearances",
                        to="profiles.profile",
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="clearances",
                        to="submissions.submission",
                    ),
                ),
            ],
        ),
    ]
