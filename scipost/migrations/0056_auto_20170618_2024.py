# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-06-18 18:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0055_auto_20170519_0937'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='registrationinvitation',
            options={'ordering': ['last_name']},
        ),
        migrations.AlterField(
            model_name='remark',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
