# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-13 22:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('commentaries', '0012_remove_commentary_specialization'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentary',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='commentary',
            name='latest_activity',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
