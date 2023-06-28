# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-30 16:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("scipost", "0015_contributor_profile"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contributor",
            name="profile",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="profiles.Profile",
            ),
        ),
    ]
