# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-05-04 19:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0053_auto_20170504_1538'),
    ]

    state_operations = [
        migrations.DeleteModel(
            name='NewsItem',
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations)
    ]
