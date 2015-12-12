# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='clarity_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='originality_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='rigour_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='significance_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='validity_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
    ]
