# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-20 17:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0026_refereeinvitation_auto_reminders_allowed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refereeinvitation',
            name='auto_reminders_allowed',
            field=models.BooleanField(default=False),
        ),
    ]