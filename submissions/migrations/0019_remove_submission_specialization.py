# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-08-11 13:39
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0018_auto_20160811_1442'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='specialization',
        ),
    ]
