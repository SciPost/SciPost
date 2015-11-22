# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0010_remove_submission_specialization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='submitted_to_journal',
            field=models.CharField(choices=[('SciPost Physics Select', 'SciPost Physics Select'), ('SciPost Physics Letters', 'SciPost Physics Letters'), ('SciPost Physics A', 'SciPostPhysics A (Atomic, Molecular and Optical Physics)'), ('SciPost Physics C', 'SciPostPhysics C (Condensed Matter Physics)'), ('SciPost Physics H', 'SciPostPhysics H (High-energy Physics)'), ('SciPost Physics M', 'SciPostPhysics M (Mathematical Physics)'), ('SciPost Physics Q', 'SciPostPhysics Q (Quantum Statistical Mechanics)'), ('SciPost Physics S', 'SciPostPhysics S (Classical Statistical and Soft Matter Physics)')], max_length=30),
        ),
    ]
