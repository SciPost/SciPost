# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-10 10:54
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0021_auto_20180310_1137'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='journal',
            name='has_issues',
        ),
        migrations.RemoveField(
            model_name='journal',
            name='has_volumes',
        ),
    ]
