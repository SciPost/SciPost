# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Funder",
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
                ("name", models.CharField(max_length=256)),
                ("acronym", models.CharField(blank=True, max_length=32, null=True)),
                ("identifier", models.CharField(max_length=200, unique=True)),
            ],
            options={
                "ordering": ["name", "acronym"],
            },
        ),
        migrations.CreateModel(
            name="Grant",
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
                ("number", models.CharField(max_length=64)),
                (
                    "recipient_name",
                    models.CharField(blank=True, max_length=64, null=True),
                ),
                (
                    "further_details",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                (
                    "funder",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="funders.Funder"
                    ),
                ),
            ],
            options={
                "ordering": ["funder", "recipient", "recipient_name", "number"],
            },
        ),
    ]
