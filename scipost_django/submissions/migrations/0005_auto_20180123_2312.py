# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-23 22:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0004_merge_20180123_2041'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eicrecommendation',
            options={'ordering': ['version']},
        ),
        migrations.AddField(
            model_name='eicrecommendation',
            name='version',
            field=models.SmallIntegerField(default=1),
        ),
    ]