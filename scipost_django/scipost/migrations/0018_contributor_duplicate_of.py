# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-11-17 17:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("scipost", "0017_auto_20181115_2150"),
    ]

    operations = [
        migrations.AddField(
            model_name="contributor",
            name="duplicate_of",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="duplicates",
                to="scipost.Contributor",
            ),
        ),
    ]
