# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-05 19:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0030_merge_20180519_2204"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="abstract_jats",
            field=models.TextField(
                blank=True,
                default="",
                help_text="JATS version of abstract for Crossref deposit",
            ),
        ),
    ]
