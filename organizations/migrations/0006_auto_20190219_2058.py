# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-02-19 19:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0005_auto_20190219_2057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationevent',
            name='noted_on',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
