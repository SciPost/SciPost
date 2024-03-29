# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-25 20:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("funders", "0004_auto_20180425_2146"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grant",
            name="funder",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="grants",
                to="funders.Funder",
            ),
        ),
        migrations.AlterField(
            model_name="grant",
            name="further_details",
            field=models.CharField(blank=True, default="", max_length=256),
        ),
        migrations.AlterField(
            model_name="grant",
            name="recipient",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="grants",
                to="scipost.Contributor",
            ),
        ),
        migrations.AlterField(
            model_name="grant",
            name="recipient_name",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
