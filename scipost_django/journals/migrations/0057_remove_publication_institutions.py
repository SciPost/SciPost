# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-04-04 15:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0056_publicationauthorstable_profile"),
    ]

    operations = [
        # Deprecation of affiliations app 2019-04-04
        # migrations.RemoveField(
        #     model_name='publication',
        #     name='institutions',
        # ),
    ]
