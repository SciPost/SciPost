# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-08 07:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metacore', '0003_auto_20180508_0911'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journal',
            name='last_update',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
