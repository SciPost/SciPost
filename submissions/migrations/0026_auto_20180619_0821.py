# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-19 06:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('preprints', '0004_auto_20180619_0821'),
        ('submissions', '0025_auto_20180520_1430'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='preprint2',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='submission2', to='preprints.Preprint'),
        ),
    ]
