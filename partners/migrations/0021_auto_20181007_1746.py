# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-07 15:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0020_auto_20181007_1649'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='partner',
            name='institution',
        ),
        migrations.AlterField(
            model_name='contact',
            name='partners',
            field=models.ManyToManyField(help_text='All Partners (+related Organizations) the Contact is related to.', to='partners.Partner'),
        ),
    ]
