# Generated by Django 5.0.12 on 2025-03-05 12:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ontology", "0009_populate_specialty_topics"),
        ("profiles", "0043_alter_profile_first_name_original_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TopicInterest",
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
                ("weight", models.FloatField(default=0.0)),
                (
                    "source",
                    models.CharField(
                        choices=[("manual", "Manual"), ("automatic", "Automatic")],
                        default="manual",
                        max_length=16,
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="profiles.profile",
                    ),
                ),
                (
                    "topic",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interests",
                        to="ontology.topic",
                    ),
                ),
            ],
            options={
                "default_related_name": "topic_interests",
            },
        ),
        migrations.AddConstraint(
            model_name="topicinterest",
            constraint=models.UniqueConstraint(
                fields=("profile", "topic", "source"),
                name="unique_topic_interest_source",
            ),
        ),
        migrations.AddConstraint(
            model_name="topicinterest",
            constraint=models.CheckConstraint(
                check=models.Q(("weight__gte", -1), ("weight__lte", 1)),
                name="weight_range",
                violation_error_message="Weight must be in the range [-1, 1]",
            ),
        ),
    ]
