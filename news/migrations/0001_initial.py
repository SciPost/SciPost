# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NewsItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('headline', models.CharField(max_length=300)),
                ('blurb', models.TextField()),
                ('followup_link', models.URLField(blank=True)),
                ('followup_link_text', models.CharField(blank=True, max_length=300)),
                ('on_homepage', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['-date'],
                'db_table': 'scipost_newsitem',
            },
        ),
    ]
