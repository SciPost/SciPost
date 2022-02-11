# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-29 17:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0006_merge_20180123_2040"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reference",
            name="vor",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AlterField(
            model_name="reference",
            name="vor_url",
            field=models.URLField(blank=True),
        ),
    ]
