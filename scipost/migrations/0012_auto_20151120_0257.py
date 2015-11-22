# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0011_auto_20151120_0237'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='specialization',
            field=models.CharField(max_length=1, choices=[('A', 'Atomic, Molecular and Optical Physics'), ('C', 'Condensed Matter Physics'), ('H', 'High-Energy Physics'), ('M', 'Mathematical Physics'), ('N', 'Nuclear Physics'), ('Q', 'Quantum Statistical Mechanics'), ('S', 'Statistical and Soft Matter Physics')], default='A'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='submitted_to_journal',
            field=models.CharField(max_length=30, choices=[('SciPost Physics Select', 'SciPost Physics Select'), ('SciPost Physics Letters', 'SciPost Physics Letters'), ('SciPost Physics E', 'SciPost Physics E (Experimental)'), ('SciPost Physics T', 'SciPost Physics T (Theoretical)'), ('SciPost Physics C', 'SciPost Physics C (Computational)')]),
        ),
    ]
