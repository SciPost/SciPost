# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-15 07:01
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0030_merge_20170730_0935'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contact',
            old_name='activation_key',
            new_name='_activation_key',
        ),
    ]
