# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-25 19:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("funders", "0002_auto_20171229_1435"),
    ]

    operations = [
        migrations.AlterField(
            model_name="funder",
            name="acronym",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
