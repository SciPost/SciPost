# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-22 12:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0017_auto_20180922_1603'),
        ('petitions', '0007_remove_petitionsignatory_organization_tbd'),
    ]

    operations = [
        migrations.RenameField(
            model_name='petitionsignatory',
            old_name='org',
            new_name='organization',
        ),
    ]
