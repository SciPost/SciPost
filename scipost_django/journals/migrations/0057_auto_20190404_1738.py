# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-04-04 15:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0056_publicationauthorstable_profile"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publication",
            name="latest_activity",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
