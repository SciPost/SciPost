# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-07-10 07:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0027_auto_20170710_0805'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='deposit',
            options={'ordering': ['-timestamp']},
        ),
        migrations.AddField(
            model_name='deposit',
            name='deposit_successful',
            field=models.NullBooleanField(default=None),
        ),
    ]
