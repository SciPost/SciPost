# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-12 18:50
from __future__ import unicode_literals

from django.db import migrations


def transfer_publication_authors_to_separate_table(apps, schema_editor):
    Contributor = apps.get_model('scipost', 'Contributor')
    Publication = apps.get_model('journals', 'Publication')
    UnregisteredAuthor = apps.get_model('journals', 'UnregisteredAuthor')
    PublicationAuthorsTable = apps.get_model('journals', 'PublicationAuthorsTable')

    for publication in Publication.objects.all():
        registered_authors = Contributor.objects.filter(publications_old__id=publication.id)
        unregistered_authors = UnregisteredAuthor.objects.filter(publications_old__id=publication.id)

        count = 1
        for author in registered_authors:
            PublicationAuthorsTable.objects.create(
                publication=publication,
                contributor=author,
                order=count,
            )
            count += 1

        for author in unregistered_authors:
            PublicationAuthorsTable.objects.create(
                publication=publication,
                unregistered_author=author,
                order=count,
            )
            count += 1


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0011_auto_20180212_1950'),
    ]

    operations = [
        migrations.RunPython(transfer_publication_authors_to_separate_table)
    ]
