# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-08-02 13:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0013_auto_20160802_0534'),
    ]

    operations = [
        migrations.AlterField(
            model_name='editorialassignment',
            name='refusal_reason',
            field=models.CharField(blank=True, choices=[('BUS', 'Too busy'), ('VAC', 'Away on vacation'), ('COI', 'Conflict of interest: coauthor in last 5 years'), ('CCC', 'Conflict of interest: close colleague'), ('NIR', 'Cannot give an impartial assessment'), ('NIE', 'Not interested enough'), ('DNP', 'SciPost should not even consider this paper')], max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='refereeinvitation',
            name='refusal_reason',
            field=models.CharField(blank=True, choices=[('BUS', 'Too busy'), ('VAC', 'Away on vacation'), ('COI', 'Conflict of interest: coauthor in last 5 years'), ('CCC', 'Conflict of interest: close colleague'), ('NIR', 'Cannot give an impartial assessment'), ('NIE', 'Not interested enough'), ('DNP', 'SciPost should not even consider this paper')], max_length=3, null=True),
        ),
    ]
