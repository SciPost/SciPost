# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commentaries', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commentary',
            name='clarity_rating',
            field=models.DecimalField(max_digits=3, null=True, decimal_places=0, default=0),
        ),
        migrations.AlterField(
            model_name='commentary',
            name='originality_rating',
            field=models.DecimalField(max_digits=3, null=True, decimal_places=0, default=0),
        ),
        migrations.AlterField(
            model_name='commentary',
            name='rigour_rating',
            field=models.DecimalField(max_digits=3, null=True, decimal_places=0, default=0),
        ),
        migrations.AlterField(
            model_name='commentary',
            name='significance_rating',
            field=models.DecimalField(max_digits=3, null=True, decimal_places=0, default=0),
        ),
        migrations.AlterField(
            model_name='commentary',
            name='validity_rating',
            field=models.DecimalField(max_digits=3, null=True, decimal_places=0, default=0),
        ),
    ]
