# Generated by Django 2.2.16 on 2021-01-24 13:24

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0105_auto_20210114_1555'),
    ]

    operations = [
        migrations.AddField(
            model_name='journal',
            name='cf_metrics',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
    ]