# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-15 20:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proceedings', '0001_initial'),
        ('submissions', '0079_auto_20171014_0951'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='proceedings',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='proceedings.Proceedings'),
        ),
    ]
