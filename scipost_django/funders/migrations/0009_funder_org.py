# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-22 13:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0002_populate_from_partners_org"),
        ("funders", "0008_auto_20180715_0521"),
    ]

    operations = [
        migrations.AddField(
            model_name="funder",
            name="org",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="organizations.Organization",
            ),
        ),
    ]
