# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-22 13:11
from __future__ import unicode_literals

from django.db import migrations


def repopulate_organization_field(apps, schema_editor):
    Funder = apps.get_model('funders', 'Funder')
    Organization = apps.get_model('organizations', 'Organization')

    for funder in Funder.objects.filter(organization__isnull=False):
        funder.org = Organization.objects.get(name=funder.organization.name)
        funder.save()


class Migration(migrations.Migration):

    dependencies = [
        ('funders', '0009_funder_org'),
    ]

    operations = [
        migrations.RunPython(repopulate_organization_field,
                             reverse_code=migrations.RunPython.noop),
    ]
