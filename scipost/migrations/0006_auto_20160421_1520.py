# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-04-21 13:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0005_auto_20160419_2157'),
    ]

    operations = [
        migrations.RenameField(
            model_name='registrationinvitation',
            old_name='email_address',
            new_name='email',
        ),
    ]
