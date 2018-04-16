# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-27 17:33
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0008_merge_20180322_1031'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contributor',
            name='orcid_id',
            field=models.CharField(blank=True, max_length=20, validators=[django.core.validators.RegexValidator('^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]{1}$', 'Please follow the ORCID format, e.g.: 0000-0001-2345-6789')], verbose_name='ORCID id'),
        ),
    ]
