# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-02 18:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0020_auto_20180426_1247'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='refereeing_cycle',
            field=models.CharField(choices=[('', 'Cycle undetermined'), ('default', 'Default cycle'), ('short', 'Short cycle'), ('direct_rec', 'Direct editorial recommendation')], default='default', max_length=30),
        ),
    ]
