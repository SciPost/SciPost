# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-30 05:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0002_auto_20180916_1643"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlternativeEmail",
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
                ("email", models.EmailField(max_length=254)),
                ("still_valid", models.BooleanField(default=True)),
            ],
        ),
        migrations.AlterField(
            model_name="profile",
            name="email",
            field=models.EmailField(max_length=254),
        ),
        migrations.AddField(
            model_name="alternativeemail",
            name="profile",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="profiles.Profile"
            ),
        ),
    ]
