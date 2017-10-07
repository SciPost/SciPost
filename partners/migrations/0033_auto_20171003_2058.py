# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-03 18:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0065_authorshipclaim_publication'),
        ('partners', '0032_auto_20170829_0727'),
    ]

    operations = [
        migrations.CreateModel(
            name='Petition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256)),
                ('slug', models.SlugField()),
                ('headline', models.CharField(max_length=256)),
                ('statement', models.TextField()),
                ('signatories', models.ManyToManyField(related_name='petitions', to='scipost.Contributor')),
            ],
        ),
    ]
