# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-18 14:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0004_auto_20180212_1932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registrationinvitation',
            name='first_name',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='registrationinvitation',
            name='last_name',
            field=models.CharField(max_length=30),
        ),
    ]
