# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-22 14:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0017_auto_20180922_1603'),
        ('funders', '0011_remove_funder_organization'),
    ]

    operations = [
        migrations.RenameField(
            model_name='funder',
            old_name='org',
            new_name='organization',
        ),
    ]
