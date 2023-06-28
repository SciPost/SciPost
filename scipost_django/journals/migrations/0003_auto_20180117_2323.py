# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-17 22:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0002_auto_20171229_1435"),
    ]

    operations = [
        migrations.AlterField(
            model_name="deposit",
            name="doi_batch_id",
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name="deposit",
            name="metadata_xml",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="deposit",
            name="response_text",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="deposit",
            name="timestamp",
            field=models.CharField(max_length=40),
        ),
    ]
