# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-29 06:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("colleges", "0003_prospectivefellow_prospectivefellowevent"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="prospectivefellow",
            options={"ordering": ["last_name"]},
        ),
    ]
