# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-03 19:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0033_auto_20171003_2058'),
    ]

    operations = [
        migrations.AlterField(
            model_name='petition',
            name='signatories',
            field=models.ManyToManyField(blank=True, related_name='petitions', to='scipost.Contributor'),
        ),
    ]
