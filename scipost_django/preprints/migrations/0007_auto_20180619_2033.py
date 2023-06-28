# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-19 18:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("preprints", "0006_remove_preprint_submission"),
    ]

    operations = [
        migrations.AlterField(
            model_name="preprint",
            name="identifier_w_vn_nr",
            field=models.CharField(db_index=True, max_length=25, unique=True),
        ),
    ]
