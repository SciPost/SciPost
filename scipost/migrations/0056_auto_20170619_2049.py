# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-06-19 18:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0055_auto_20170519_0937'),
    ]

    operations = [
        migrations.AlterField(
            model_name='draftinvitation',
            name='date_drafted',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='draftinvitation',
            name='first_name',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='draftinvitation',
            name='last_name',
            field=models.CharField(max_length=30),
        ),
    ]
