# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-11-10 05:41
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0051_auto_20181102_1332'),
    ]

    operations = [
        migrations.AddField(
            model_name='journal',
            name='refereeing_period',
            field=models.DurationField(default=datetime.timedelta(28)),
        ),
    ]