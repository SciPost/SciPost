# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-13 19:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('preprints', '0007_auto_20180619_2033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='preprint',
            name='url',
            field=models.URLField(blank=True),
        ),
    ]
