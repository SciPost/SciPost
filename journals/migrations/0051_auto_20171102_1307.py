# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-02 12:07
from __future__ import unicode_literals

from django.db import migrations


def fill_publications(apps, schema_editor):
    """
    Add all Institutes to a Publication, assuming all Contributors Affiliations are
    active at moment of publication.
    """
    Publication = apps.get_model('journals', 'Publication')
    for publication in Publication.objects.all():
        for author in publication.authors.all():
            for affiliation in author.affiliations.all():
                publication.institutes.add(affiliation.institute)


def return_none(*args, **kwargs):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0050_publication_institutes'),
    ]

    operations = [
        migrations.RunPython(fill_publications, return_none),
    ]
