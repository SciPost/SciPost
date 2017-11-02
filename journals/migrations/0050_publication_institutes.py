# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-02 12:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('affiliations', '0007_auto_20171102_1256'),
        ('journals', '0049_auto_20171101_2000'),
    ]

    operations = [
        migrations.AddField(
            model_name='publication',
            name='institutes',
            field=models.ManyToManyField(blank=True, related_name='publications', to='affiliations.Institute'),
        ),
    ]
