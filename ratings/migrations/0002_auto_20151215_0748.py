# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ratings', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorreplyrating',
            name='clarity',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='authorreplyrating',
            name='importance',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='authorreplyrating',
            name='relevance',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='authorreplyrating',
            name='rigour',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='authorreplyrating',
            name='validity',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='commentaryrating',
            name='clarity',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='commentaryrating',
            name='originality',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='commentaryrating',
            name='rigour',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='commentaryrating',
            name='significance',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='commentaryrating',
            name='validity',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='commentrating',
            name='clarity',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='commentrating',
            name='importance',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='commentrating',
            name='relevance',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='commentrating',
            name='rigour',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='commentrating',
            name='validity',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='reportrating',
            name='clarity',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='reportrating',
            name='importance',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='reportrating',
            name='relevance',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='reportrating',
            name='rigour',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='reportrating',
            name='validity',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='submissionrating',
            name='clarity',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='submissionrating',
            name='originality',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='submissionrating',
            name='rigour',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='submissionrating',
            name='significance',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
        migrations.AlterField(
            model_name='submissionrating',
            name='validity',
            field=models.PositiveSmallIntegerField(verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True, default=0),
        ),
    ]
