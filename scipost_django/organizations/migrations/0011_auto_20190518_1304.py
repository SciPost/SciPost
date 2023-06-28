# Generated by Django 2.1.8 on 2019-05-18 11:04

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0010_auto_20190223_1406"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organization",
            name="crossref_json",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                blank=True, default=dict, null=True
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="grid_json",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                blank=True, default=dict, null=True
            ),
        ),
    ]
