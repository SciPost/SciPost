# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-08-13 12:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0015_auto_20160811_1305'),
    ]

    operations = [
        migrations.CreateModel(
            name='Remark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('remark', models.TextField()),
                ('contributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scipost.Contributor')),
            ],
        ),
    ]
