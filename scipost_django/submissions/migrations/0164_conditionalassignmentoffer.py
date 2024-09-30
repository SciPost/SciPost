# Generated by Django 4.2.15 on 2024-09-30 11:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        (
            "scipost",
            "0041_alter_remark_contributor_alter_remark_recommendation_and_more",
        ),
        ("submissions", "0163_submission_assignment_deadline"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConditionalAssignmentOffer",
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
                ("offered_on", models.DateTimeField(auto_now_add=True)),
                ("offered_until", models.DateTimeField(blank=True, null=True)),
                ("accepted_on", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("offered", "Offered"),
                            ("accepted", "Accepted"),
                            ("declined", "Declined"),
                            ("fulfilled", "Fulfilled"),
                        ],
                        default="offered",
                        max_length=16,
                    ),
                ),
                ("condition_type", models.CharField(choices=[], max_length=32)),
                ("condition_details", models.JSONField(default=dict)),
                (
                    "accepted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="conditional_assignments_accepted",
                        to="scipost.contributor",
                    ),
                ),
                (
                    "offered_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conditional_assignments_offered",
                        to="scipost.contributor",
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
                "ordering": ["-offered_on"],
                "default_related_name": "conditional_assignment_offers",
            },
        ),
        migrations.AddConstraint(
            model_name="conditionalassignmentoffer",
            constraint=models.UniqueConstraint(
                fields=("submission", "offered_by", "condition_type"),
                name="unique_offer_type_per_submission_fellow",
            ),
        ),
    ]
