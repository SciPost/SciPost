# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-29 10:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_auto_20180916_1643'),
        ('scipost', '0014_auto_20180414_2218'),
    ]

    operations = [
        migrations.AddField(
            model_name='contributor',
            name='profile',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='profiles.Profile'),
        ),
    ]
