# Generated by Django 3.2.5 on 2021-10-21 04:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0111_remove_submission_voting_fellows"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submissionevent",
            name="event",
            field=models.CharField(
                choices=[
                    ("gen", "General comment"),
                    ("edad", "Comment for EdAdmin"),
                    ("eic", "Comment for Editor-in-charge"),
                    ("auth", "Comment for author"),
                ],
                default="gen",
                max_length=4,
            ),
        ),
    ]
