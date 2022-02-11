# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-23 11:35
from __future__ import unicode_literals

from django.db import migrations


def set_site_name(apps, schema_editor):
    Sites = apps.get_model("sites", "Site")
    try:
        site = Sites.objects.get(id=1)
    except Sites.DoesNotExist:
        site = Sites(id=1)
    site.name = "SciPost"
    site.domain = "scipost.org"
    site.save()


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.RunPython(set_site_name, reverse_code=migrations.RunPython.noop),
    ]
