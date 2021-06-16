# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-12 18:57
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0003_productionuser_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productionuser',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='production_user', to=settings.AUTH_USER_MODEL),
        ),
    ]