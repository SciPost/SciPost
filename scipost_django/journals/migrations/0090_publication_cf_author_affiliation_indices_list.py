# Generated by Django 2.2.11 on 2020-08-21 12:08

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0089_journal_submission_allowed"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="cf_author_affiliation_indices_list",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=django.contrib.postgres.fields.ArrayField(
                    base_field=models.PositiveSmallIntegerField(blank=True),
                    default=list,
                    size=None,
                ),
                default=list,
                size=None,
            ),
        ),
    ]
