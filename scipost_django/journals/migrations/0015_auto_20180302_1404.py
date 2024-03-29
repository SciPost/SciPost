# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-02 13:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0014_publication_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publication",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("prepub", "Pre-published"),
                    ("pub", "Published"),
                ],
                default="draft",
                max_length=8,
            ),
        ),
    ]
