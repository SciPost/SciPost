# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-06-24 18:03
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0057_merge_20170624_1943'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contributor',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]
