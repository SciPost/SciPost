# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-02 07:43
from __future__ import unicode_literals

from django.db import migrations


def fill_affiliations(apps, schema_editor):
    Contributor = apps.get_model('scipost', 'Contributor')
    Affiliation = apps.get_model('affiliations', 'Affiliation')
    for contributor in Contributor.objects.all():
        Affiliation.objects.get_or_create(
            institute=contributor.old_affiliation_fk, contributor=contributor)


def return_none(*args, **kwargs):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('affiliations', '0005_affiliation'),
        ('scipost', '0069_auto_20171102_0840'),
    ]

    operations = [
        migrations.RunPython(fill_affiliations, return_none),
    ]
