# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-08-11 22:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_newsitem_on_homepage'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='newsitem',
            options={'ordering': ['-date']},
        ),
    ]
