# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-12 18:47
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0008_auto_20180203_1229"),
    ]

    operations = [
        migrations.RenameField(
            model_name="publication",
            old_name="authors",
            new_name="authors_old",
        ),
        migrations.RenameField(
            model_name="publication",
            old_name="authors_unregistered",
            new_name="authors_unregistered_old",
        ),
    ]
