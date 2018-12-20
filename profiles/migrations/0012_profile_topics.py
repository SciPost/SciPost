# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-28 19:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ontology', '0005_auto_20181028_2038'),
        ('profiles', '0011_auto_20181006_2341'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='topics',
            field=models.ManyToManyField(blank=True, to='ontology.Topic'),
        ),
    ]