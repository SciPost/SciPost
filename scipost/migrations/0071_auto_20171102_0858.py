# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-02 07:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0070_remove_contributor_old_affiliation_fk'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contributor',
            name='old_affiliation',
        ),
        migrations.RemoveField(
            model_name='contributor',
            name='old_country_of_employment',
        ),
    ]
