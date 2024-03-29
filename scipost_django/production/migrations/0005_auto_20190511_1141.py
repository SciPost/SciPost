# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-11 09:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("production", "0004_auto_20180112_1957"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productionstream",
            name="invitations_officer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="invitations_officer_streams",
                to="production.ProductionUser",
            ),
        ),
        migrations.AlterField(
            model_name="productionstream",
            name="officer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="streams",
                to="production.ProductionUser",
            ),
        ),
        migrations.AlterField(
            model_name="productionstream",
            name="supervisor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="supervised_streams",
                to="production.ProductionUser",
            ),
        ),
    ]
