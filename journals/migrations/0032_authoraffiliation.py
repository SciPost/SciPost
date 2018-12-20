# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-07 18:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0005_organization'),
        ('scipost', '0014_auto_20180414_2218'),
        ('journals', '0031_publication_abstract_jats'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorAffiliation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=64)),
                ('last_name', models.CharField(max_length=64)),
                ('contributor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='scipost.Contributor')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='partners.Organization')),
                ('publication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='journals.Publication')),
                ('unregistered_author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='journals.UnregisteredAuthor')),
            ],
        ),
    ]