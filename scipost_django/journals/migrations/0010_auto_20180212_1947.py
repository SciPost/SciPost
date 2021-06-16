# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-12 18:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0009_auto_20180212_1947'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publication',
            name='authors_old',
            field=models.ManyToManyField(blank=True, related_name='publications_old', to='scipost.Contributor'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='authors_unregistered_old',
            field=models.ManyToManyField(blank=True, related_name='publications_old', to='journals.UnregisteredAuthor'),
        ),
    ]