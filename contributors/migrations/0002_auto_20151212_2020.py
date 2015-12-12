# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributors', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contributor',
            name='comment_originality_rating',
        ),
        migrations.RemoveField(
            model_name='contributor',
            name='comment_significance_rating',
        ),
        migrations.RemoveField(
            model_name='contributor',
            name='nr_comment_originality_ratings',
        ),
        migrations.RemoveField(
            model_name='contributor',
            name='nr_comment_significance_ratings',
        ),
        migrations.RemoveField(
            model_name='contributor',
            name='nr_report_originality_ratings',
        ),
        migrations.RemoveField(
            model_name='contributor',
            name='nr_report_significance_ratings',
        ),
        migrations.RemoveField(
            model_name='contributor',
            name='report_originality_rating',
        ),
        migrations.RemoveField(
            model_name='contributor',
            name='report_significance_rating',
        ),
        migrations.AddField(
            model_name='contributor',
            name='comment_importance_rating',
            field=models.DecimalField(max_digits=3, default=0, decimal_places=0),
        ),
        migrations.AddField(
            model_name='contributor',
            name='comment_relevance_rating',
            field=models.DecimalField(max_digits=3, default=0, decimal_places=0),
        ),
        migrations.AddField(
            model_name='contributor',
            name='nr_comment_importance_ratings',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='contributor',
            name='nr_comment_relevance_ratings',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='contributor',
            name='nr_report_importance_ratings',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='contributor',
            name='nr_report_relevance_ratings',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='contributor',
            name='report_importance_rating',
            field=models.DecimalField(max_digits=3, default=0, decimal_places=0),
        ),
        migrations.AddField(
            model_name='contributor',
            name='report_relevance_rating',
            field=models.DecimalField(max_digits=3, default=0, decimal_places=0),
        ),
    ]
