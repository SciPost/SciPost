# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-20 18:08
from __future__ import unicode_literals

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0045_auto_20180927_2055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orgpubfraction',
            name='fraction',
            field=models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=4),
        ),
    ]