# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-02-22 10:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0007_auto_20190221_0553"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="contact",
            options={"ordering": ["user__last_name", "user__first_name"]},
        ),
    ]
