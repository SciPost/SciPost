# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-06 07:07
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("forums", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="forum",
            options={
                "ordering": ["name"],
                "permissions": [("can_view_forum", "Can view Forum")],
            },
        ),
    ]
