# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-18 15:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0013_auto_20180715_0938'),
        ('journals', '0035_orgpubfraction'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='orgpubfraction',
            unique_together=set([('organization', 'publication')]),
        ),
    ]