# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-01 19:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('affiliations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='affiliation',
            name='acronym',
            field=models.CharField(blank=True, max_length=16),
        ),
    ]
