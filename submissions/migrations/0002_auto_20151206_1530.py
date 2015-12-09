# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='submitted_to_journal',
            field=models.CharField(max_length=30, choices=[('SciPost Physics Select', 'SciPost Physics Select'), ('SciPost Physics Letters', 'SciPost Physics Letters'), ('SciPost Physics X', 'SciPost Physics X (cross-division)'), ('SciPost Physics', 'SciPost Physics (Experimental, Theoretical and Computational)'), ('SciPost Physics Lecture Notes', 'SciPost Physics Lecture Notes')]),
        ),
    ]
