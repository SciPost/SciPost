# Generated by Django 2.1.8 on 2019-10-14 19:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0084_journal_minimal_nr_of_reports"),
        ("submissions", "0066_auto_20191005_1142"),
    ]

    operations = [
        migrations.AddField(
            model_name="eicrecommendation",
            name="for_journal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="journals.Journal",
            ),
        ),
        migrations.AlterField(
            model_name="eicrecommendation",
            name="recommendation",
            field=models.SmallIntegerField(
                choices=[
                    (None, "-"),
                    (
                        1,
                        "Surpasses expectations and criteria for this Journal (among top 10%)",
                    ),
                    (
                        2,
                        "Easily meets expectations and criteria for this Journal (among top 50%)",
                    ),
                    (3, "Meets expectations and criteria for this Journal"),
                    (-1, "Ask for minor revision"),
                    (-2, "Ask for major revision"),
                    (-3, "Reject"),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="recommendation",
            field=models.SmallIntegerField(
                blank=True,
                choices=[
                    (None, "-"),
                    (
                        1,
                        "Surpasses expectations and criteria for this Journal (among top 10%)",
                    ),
                    (
                        2,
                        "Easily meets expectations and criteria for this Journal (among top 50%)",
                    ),
                    (3, "Meets expectations and criteria for this Journal"),
                    (-1, "Ask for minor revision"),
                    (-2, "Ask for major revision"),
                    (-3, "Reject"),
                ],
                null=True,
            ),
        ),
    ]
