# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0005_auto_20151119_1447'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='submitted_to_journal',
            field=models.CharField(max_length=30, choices=[('SciPost Physics Letters', 'SciPost Physics Letters'), ('SciPost Physics', 'SciPost Physics')]),
        ),
    ]
