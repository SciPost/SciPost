# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import scipost.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Fellowship",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "latest_activity",
                    scipost.db.fields.AutoDateTimeField(
                        blank=True, default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("start_date", models.DateField(blank=True, null=True)),
                ("until_date", models.DateField(blank=True, null=True)),
                (
                    "guest",
                    models.BooleanField(default=False, verbose_name="Guest Fellowship"),
                ),
            ],
        ),
    ]
