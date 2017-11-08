# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-02 07:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0069_auto_20171102_0840'),
        ('affiliations', '0004_auto_20171101_2208'),
    ]

    operations = [
        migrations.CreateModel(
            name='Affiliation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('contributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='affiliations', to='scipost.Contributor')),
                ('institute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='affiliations', to='affiliations.Institution')),
            ],
            options={
                'default_related_name': 'affiliations',
            },
        ),
    ]
