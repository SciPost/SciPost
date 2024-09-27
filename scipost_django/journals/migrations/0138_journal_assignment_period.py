# Generated by Django 4.2.15 on 2024-09-27 09:21

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0137_alter_journal_alternative_journals"),
    ]

    operations = [
        migrations.AddField(
            model_name="journal",
            name="assignment_period",
            field=models.DurationField(default=datetime.timedelta(days=28)),
        ),
    ]
