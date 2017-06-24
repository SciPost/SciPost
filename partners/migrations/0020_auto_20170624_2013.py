# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-06-24 18:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0019_auto_20170624_2003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='main_contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='partner_main_contact', to='partners.Contact'),
        ),
    ]
