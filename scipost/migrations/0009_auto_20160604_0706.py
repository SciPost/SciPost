# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-06-04 05:06
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0008_auto_20160531_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contributor',
            name='specializations',
            field=django.contrib.postgres.fields.jsonb.JSONField(default='{}'),
        ),
    ]
