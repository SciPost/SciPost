# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-30 17:39
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0034_auto_20180913_2114"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="editorialassignment",
            name="old_accepted",
        ),
        migrations.RemoveField(
            model_name="editorialassignment",
            name="old_completed",
        ),
        migrations.RemoveField(
            model_name="editorialassignment",
            name="old_deprecated",
        ),
    ]
