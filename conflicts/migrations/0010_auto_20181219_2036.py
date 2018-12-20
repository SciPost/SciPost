# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-12-19 19:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0015_auto_20181118_0849'),
        ('conflicts', '0009_conflictofinterest'),
    ]

    operations = [
        migrations.AddField(
            model_name='conflictofinterest',
            name='profile',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='conflicts', to='profiles.Profile'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='conflictofinterest',
            name='related_profile',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='profiles.Profile'),
            preserve_default=False,
        ),
    ]
