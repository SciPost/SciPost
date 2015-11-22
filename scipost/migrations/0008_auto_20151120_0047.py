# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0007_auto_20151120_0027'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='specialization',
            field=models.CharField(max_length=1, choices=[('A', 'Atomic, Molecular and Optical Physics'), ('H', 'High-Energy Physics'), ('C', 'Condensed Matter Physics'), ('S', 'Statistical and Soft Matter Physics'), ('M', 'Mathematical Physics')], default='A'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='submitted_to_journal',
            field=models.CharField(max_length=30, choices=[('SciPost Physics Select', 'SciPost Physics Select'), ('SciPost Physics Letters', 'SciPost Physics Letters'), ('SciPost Physics', 'SciPost Physics')]),
        ),
    ]
