# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-14 07:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0078_auto_20171014_0945'),
    ]

    operations = [
        migrations.RenameField(
            model_name='submission',
            old_name='pool',
            new_name='fellows',
        ),
    ]
