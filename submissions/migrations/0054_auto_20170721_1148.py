# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-07-21 09:48
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0053_auto_20170721_1100'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='report',
            options={'ordering': ['-date_submitted']},
        ),
    ]
