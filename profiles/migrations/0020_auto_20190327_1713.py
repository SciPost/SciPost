# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-27 16:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0019_auto_20190327_1520'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='affiliation',
            options={'ordering': ['profile__last_name', 'profile__first_name', '-date_until']},
        ),
    ]
