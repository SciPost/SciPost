# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-15 20:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0004_remove_fellowship_affiliation'),
    ]

    operations = [
        migrations.AddField(
            model_name='fellowship',
            name='guest',
            field=models.BooleanField(default=False, verbose_name='Guest Fellowship'),
        ),
    ]
