# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0008_auto_20151120_0047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='specialization',
            field=models.CharField(max_length=1, choices=[('A', 'Atomic, Molecular and Optical Physics'), ('H', 'High-Energy Physics'), ('C', 'Condensed Matter Physics'), ('S', 'Statistical and Soft Matter Physics'), ('M', 'Mathematical Physics')]),
        ),
        migrations.AlterField(
            model_name='submission',
            name='submitted_to_journal',
            field=models.CharField(max_length=30, choices=[('SciPost Physics Select', 'SciPost Physics Select'), ('SciPost Physics Letters', 'SciPost Physics Letters'), ('SciPost Physics A', 'SciPostPhysics A'), ('SciPost Physics C', 'SciPostPhysics C'), ('SciPost Physics H', 'SciPostPhysics H'), ('SciPost Physics M', 'SciPostPhysics M'), ('SciPost Physics Q', 'SciPostPhysics Q'), ('SciPost Physics S', 'SciPostPhysics S (Classical)')]),
        ),
    ]
