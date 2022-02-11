# Generated by Django 2.2.11 on 2020-07-21 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0088_remove_submission_submission_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="code_repository_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="submission",
            name="data_repository_url",
            field=models.URLField(blank=True),
        ),
    ]
