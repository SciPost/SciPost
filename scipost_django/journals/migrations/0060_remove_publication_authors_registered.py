# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-04-04 20:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0059_merge_20190404_2000"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="publication",
            name="authors_registered",
        ),
    ]
