# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-22 11:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0002_populate_from_partners_org'),
        ('petitions', '0004_auto_20180922_1357'),
    ]

    operations = [
        migrations.AddField(
            model_name='petitionsignatory',
            name='org',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='petition_signatories', to='organizations.Organization'),
        ),
    ]
