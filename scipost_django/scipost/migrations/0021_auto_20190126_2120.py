# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-01-26 20:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("scipost", "0020_auto_20190126_2058"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="remark",
            options={"ordering": ["date"]},
        ),
    ]
