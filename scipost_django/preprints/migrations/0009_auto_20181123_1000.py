# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-11-23 09:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("preprints", "0008_auto_20180913_2112"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="preprint",
            options={"ordering": ["-identifier_w_vn_nr"]},
        ),
    ]
