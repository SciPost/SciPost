# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-03 08:18
from __future__ import unicode_literals

from django.db import migrations, models


def null_to_blank(apps, schema_editor):
    Publication = apps.get_model('journals', 'Publication')
    for pub in Publication.objects.all():
        if pub.BiBTeX_entry is None:
            pub.BiBTeX_entry = ''
        if pub.metadata_xml is None:
            pub.metadata_xml = ''
        pub.save()


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0015_auto_20180302_1404'),
    ]

    operations = [
        migrations.RunPython(null_to_blank),
        migrations.AlterField(
            model_name='publication',
            name='BiBTeX_entry',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='publication',
            name='metadata_xml',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
    ]
