# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('colleges', '0001_initial'),
        ('scipost', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fellowship',
            name='contributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fellowships', to='scipost.Contributor'),
        ),
        migrations.AlterUniqueTogether(
            name='fellowship',
            unique_together=set([('contributor', 'start_date', 'until_date')]),
        ),
    ]
