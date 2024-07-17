# Generated by Django 4.2.10 on 2024-05-21 12:39

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mails", "0008_maillog_cc_recipients"),
    ]

    operations = [
        migrations.AddField(
            model_name="maillog",
            name="sent_to",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.EmailField(max_length=254),
                blank=True,
                null=True,
                size=None,
            ),
        ),
        migrations.AddField(
            model_name="maillog",
            name="type",
            field=models.CharField(
                choices=[("single", "Single"), ("bulk", "Bulk")],
                default="single",
                max_length=64,
            ),
        ),
    ]