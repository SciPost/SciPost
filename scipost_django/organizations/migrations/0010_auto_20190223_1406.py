# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-02-23 13:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0009_auto_20190223_1001"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="organizationevent",
            options={"ordering": ["-noted_on", "organization"]},
        ),
    ]
