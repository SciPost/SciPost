# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-11 19:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0006_auto_20181008_1629'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subsidy',
            options={'ordering': ['-date'], 'verbose_name_plural': 'subsidies'},
        ),
    ]
