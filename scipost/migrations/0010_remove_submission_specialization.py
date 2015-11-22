# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0009_auto_20151120_0232'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='specialization',
        ),
    ]
