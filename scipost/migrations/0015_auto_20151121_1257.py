# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0014_auto_20151120_0306'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='specialization',
            field=models.CharField(max_length=1, choices=[('A', 'Atomic, Molecular and Optical Physics'), ('C', 'Condensed Matter Physics'), ('G', 'Gravitation, Cosmology and Astroparticle Physics'), ('H', 'High-Energy Physics'), ('M', 'Mathematical Physics'), ('N', 'Nuclear Physics'), ('Q', 'Quantum Statistical Mechanics'), ('S', 'Statistical and Soft Matter Physics')]),
        ),
        migrations.AlterField(
            model_name='submission',
            name='submitted_to_journal',
            field=models.CharField(max_length=30, choices=[('SciPost Physics Select', 'SciPost Physics Select'), ('SciPost Physics Letters', 'SciPost Physics Letters'), ('SciPost Physics X', 'SciPost Physics X (cross-division)'), ('SciPost Physics E', 'SciPost Physics E (Experimental)'), ('SciPost Physics T', 'SciPost Physics T (Theoretical)'), ('SciPost Physics C', 'SciPost Physics C (Computational)')]),
        ),
    ]
