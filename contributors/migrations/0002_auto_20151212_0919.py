# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contributor',
            name='nr_comments',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='contributor',
            name='nr_reports',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
