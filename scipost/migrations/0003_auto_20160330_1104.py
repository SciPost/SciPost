# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-30 09:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0002_auto_20160329_2225'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contributor',
            name='vetted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contrib_vetted_by', to='scipost.Contributor'),
        ),
    ]
