# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-16 14:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="profile",
            options={"ordering": ["last_name"]},
        ),
    ]
