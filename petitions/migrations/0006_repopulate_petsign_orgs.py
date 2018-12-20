# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-22 12:05
from __future__ import unicode_literals

from django.db import migrations


def repopulate_organization_field(apps, schema_editor):
    PetitionSignatory = apps.get_model('petitions', 'PetitionSignatory')
    Organization = apps.get_model('organizations', 'Organization')

    for petsign in PetitionSignatory.objects.all():
        if petsign.organization_tbd:
            org = Organization.objects.get(name=petsign.organization_tbd.name)
            petsign.org = org
            petsign.save()


class Migration(migrations.Migration):

    dependencies = [
        ('petitions', '0005_petitionsignatory_organization'),
    ]

    operations = [
        migrations.RunPython(repopulate_organization_field,
                             reverse_code=migrations.RunPython.noop),
    ]