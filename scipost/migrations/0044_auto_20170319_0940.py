# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-19 08:40
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0043_auto_20170318_2237'),
    ]

    operations = [
        migrations.RenameField(
            model_name='editorialcollegemember',
            old_name='discipline',
            new_name='college',
        ),
    ]
