# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorreply',
            name='clarity_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='authorreply',
            name='originality_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='authorreply',
            name='rigour_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='authorreply',
            name='significance_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='authorreply',
            name='validity_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='clarity_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='originality_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='rigour_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='significance_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='validity_rating',
            field=models.DecimalField(default=0, decimal_places=0, max_digits=3, null=True),
        ),
    ]
