# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-01 20:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0066_contributor__affiliation'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contributor',
            old_name='affiliation',
            new_name='old_affiliation',
        ),
        migrations.RenameField(
            model_name='contributor',
            old_name='country_of_employment',
            new_name='old_country_of_employment',
        ),
        migrations.AlterField(
            model_name='contributor',
            name='_affiliation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contributors', to='affiliations.Affiliation'),
        ),
    ]
