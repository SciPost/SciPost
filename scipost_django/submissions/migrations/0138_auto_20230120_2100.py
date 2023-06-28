# Generated by Django 3.2.16 on 2023-01-20 20:00

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("colleges", "0039_nomination_add_events"),
        ("submissions", "0137_alter_qualification_expertise_level"),
    ]

    operations = [
        migrations.CreateModel(
            name="Readiness",
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
                            ("perhaps_later", "Perhaps later (if nobody else does)"),
                            (
                                "could_if_transferred",
                                "I could (but only if transferred to lower journal)",
                            ),
                            ("too_busy", "Interesting, but I'm currently too busy"),
                            (
                                "on_vacation",
                                "Interesting, but I'm currently on vacation",
                            ),
                            ("not_interested", "I won't: I'm not interested enough"),
                            ("desk_reject", "I won't, and vote for desk rejection"),
                        ],
                        max_length=32,
                    ),
                ),
                ("comments", models.TextField(blank=True)),
                ("datetime", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "fellow",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="colleges.fellowship",
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="submissions.submission",
                    ),
                ),
            ],
            options={
                "ordering": ["submission", "fellow"],
            },
        ),
        migrations.AddConstraint(
            model_name="readiness",
            constraint=models.UniqueConstraint(
                fields=("submission", "fellow"),
                name="readiness_unique_together_submission_fellow",
            ),
        ),
    ]
