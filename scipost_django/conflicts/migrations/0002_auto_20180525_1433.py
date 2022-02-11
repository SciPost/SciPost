# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-25 12:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("conflicts", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="conflictofinterest",
            name="to_unregistered",
        ),
        migrations.AddField(
            model_name="conflictofinterest",
            name="conflict_title",
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name="conflictofinterest",
            name="conflict_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="conflictofinterest",
            name="to_name",
            field=models.CharField(blank=True, max_length=128),
        ),
    ]
