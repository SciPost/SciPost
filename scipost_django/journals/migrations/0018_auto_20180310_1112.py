# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-10 10:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0017_auto_20180310_1103"),
    ]

    operations = [
        migrations.AddField(
            model_name="issue",
            name="in_journal",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="journals.Journal",
            ),
        ),
        migrations.AlterField(
            model_name="issue",
            name="in_volume",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="journals.Volume",
            ),
        ),
    ]
