# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-28 19:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ontology", "0004_relationasym_relationsym"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="topic",
            options={"ordering": ["name"]},
        ),
    ]
