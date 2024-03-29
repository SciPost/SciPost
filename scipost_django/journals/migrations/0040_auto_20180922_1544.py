# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-22 13:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0002_populate_from_partners_org"),
        ("journals", "0039_repopulate_orgs"),
    ]

    operations = [
        # migrations.RemoveField(
        #     model_name='publicationauthorstable',
        #     name='affiliations',
        # ),
        migrations.AlterUniqueTogether(
            name="orgpubfraction",
            unique_together=set([("org", "publication")]),
        ),
        # migrations.RemoveField(
        #     model_name='orgpubfraction',
        #     name='organization',
        # ),
    ]
