# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-12 07:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0008_auto_20180711_0623'),
        ('funders', '0006_auto_20180425_2212'),
    ]

    operations = [
        migrations.AddField(
            model_name='funder',
            name='organization',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='partners.Organization'),
        ),
    ]
