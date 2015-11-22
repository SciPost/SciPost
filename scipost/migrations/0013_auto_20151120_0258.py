# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0012_auto_20151120_0257'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='specialization',
            field=models.CharField(max_length=1, choices=[('A', 'Atomic, Molecular and Optical Physics'), ('C', 'Condensed Matter Physics'), ('H', 'High-Energy Physics'), ('M', 'Mathematical Physics'), ('N', 'Nuclear Physics'), ('Q', 'Quantum Statistical Mechanics'), ('S', 'Statistical and Soft Matter Physics')]),
        ),
    ]
