# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-13 19:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0033_auto_20180913_2112"),
    ]

    operations = [
        migrations.RenameField(
            model_name="editorialassignment",
            old_name="accepted",
            new_name="old_accepted",
        ),
        migrations.RenameField(
            model_name="editorialassignment",
            old_name="completed",
            new_name="old_completed",
        ),
        migrations.RenameField(
            model_name="editorialassignment",
            old_name="deprecated",
            new_name="old_deprecated",
        ),
    ]
