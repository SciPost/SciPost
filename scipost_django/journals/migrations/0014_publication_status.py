# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-02 13:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0013_auto_20180216_0850"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("prepub", "Pre-published"),
                    ("pub", "Published"),
                ],
                default="pub",
                max_length=8,
            ),
        ),
    ]
