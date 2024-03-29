# Generated by Django 2.2.11 on 2020-06-27 17:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0082_auto_20200612_0805"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="recommendation",
            field=models.SmallIntegerField(
                blank=True,
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
                    (3, "Publish (meets expectations and criteria for this Journal)"),
                    (-1, "Ask for minor revision"),
                    (-2, "Ask for major revision"),
                    (-4, "Accept in alternative Journal (see Report)"),
                    (-3, "Reject"),
                ],
                null=True,
            ),
        ),
    ]
