# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Petition",
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
                ("title", models.CharField(max_length=256)),
                ("slug", models.SlugField()),
                ("headline", models.CharField(max_length=256)),
                ("preamble", models.TextField(blank=True, null=True)),
                ("statement", models.TextField()),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="PetitionSignatory",
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
                (
                    "title",
                    models.CharField(
                        choices=[
                            ("PR", "Prof."),
                            ("DR", "Dr"),
                            ("MR", "Mr"),
                            ("MRS", "Mrs"),
                            ("MS", "Ms"),
                        ],
                        max_length=4,
                    ),
                ),
                ("first_name", models.CharField(max_length=128)),
                ("last_name", models.CharField(max_length=128)),
                ("email", models.EmailField(max_length=254)),
                (
                    "country_of_employment",
                    django_countries.fields.CountryField(max_length=2),
                ),
                (
                    "affiliation",
                    models.CharField(max_length=300, verbose_name="affiliation"),
                ),
                ("signed_on", models.DateTimeField(auto_now_add=True)),
                ("verification_key", models.CharField(blank=True, max_length=40)),
                ("verified", models.BooleanField(default=False)),
                (
                    "petition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="petition_signatories",
                        to="petitions.Petition",
                    ),
                ),
            ],
            options={
                "default_related_name": "petition_signatories",
                "ordering": ["last_name", "country_of_employment", "affiliation"],
                "verbose_name_plural": "petition signatories",
            },
        ),
    ]
