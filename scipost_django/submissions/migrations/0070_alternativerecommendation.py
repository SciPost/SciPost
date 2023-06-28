# Generated by Django 2.1.8 on 2019-10-15 15:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("scipost", "0033_auto_20191005_1142"),
        ("journals", "0084_journal_minimal_nr_of_reports"),
        ("submissions", "0069_auto_20191014_2201"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlternativeRecommendation",
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
                    "recommendation",
                    models.SmallIntegerField(
                        choices=[
                            (None, "-"),
                            (
                                1,
                                "Publish (surpasses expectations and criteria for this Journal; among top 10%)",
                            ),
                            (
                                2,
                                "Publish (easily meets expectations and criteria for this Journal; among top 50%)",
                            ),
                            (
                                3,
                                "Publish (meets expectations and criteria for this Journal)",
                            ),
                            (-1, "Ask for minor revision"),
                            (-2, "Ask for major revision"),
                            (-3, "Reject"),
                        ]
                    ),
                ),
                (
                    "eicrec",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="submissions.EICRecommendation",
                    ),
                ),
                (
                    "fellow",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scipost.Contributor",
                    ),
                ),
                (
                    "for_journal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="journals.Journal",
                    ),
                ),
            ],
        ),
    ]
