# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-20 20:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0008_auto_20180127_2208"),
    ]

    operations = [
        migrations.AlterField(
            model_name="refereeinvitation",
            name="first_name",
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name="refereeinvitation",
            name="invitation_key",
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name="refereeinvitation",
            name="last_name",
            field=models.CharField(max_length=30),
        ),
    ]
