# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-11-10 12:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0042_populate_submitted_to'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='submitted_to_journal',
        ),
    ]