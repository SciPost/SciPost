# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-05-21 13:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0005_auto_20160517_1914'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='submission',
            options={'permissions': (('can_take_editorial_actions', 'Can take editorial actions'),)},
        ),
    ]
