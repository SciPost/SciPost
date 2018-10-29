# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-17 06:46
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Journal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('ISSN_digital', models.CharField(max_length=9, validators=[django.core.validators.RegexValidator('^[0-9]{4}-[0-9]{3}[0-9X]$')])),
                ('ISSN_print', models.CharField(blank=True, max_length=9, null=True, validators=[django.core.validators.RegexValidator('^[0-9]{4}-[0-9]{3}[0-9X]$')])),
                ('last_full_sync', models.DateTimeField(blank=True, null=True)),
                ('last_cursor', models.CharField(blank=True, max_length=250, null=True)),
                ('last_errors', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
