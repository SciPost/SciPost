# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-12-19 19:40
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("conflicts", "0010_auto_20181219_2036"),
    ]

    operations = [
        migrations.RenameField(
            model_name="conflictofinterest",
            old_name="title",
            new_name="header",
        ),
    ]
