# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-08 08:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0033_publicationauthorstable_affiliations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authoraffiliation',
            name='contributor',
        ),
        # migrations.RemoveField(
        #     model_name='authoraffiliation',
        #     name='organization',
        # ),
        migrations.RemoveField(
            model_name='authoraffiliation',
            name='publication',
        ),
        migrations.RemoveField(
            model_name='authoraffiliation',
            name='unregistered_author',
        ),
        migrations.DeleteModel(
            name='AuthorAffiliation',
        ),
    ]
