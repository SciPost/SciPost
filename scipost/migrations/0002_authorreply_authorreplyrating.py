# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorReply',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('status', models.SmallIntegerField(default=0)),
                ('reply_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(max_digits=3, decimal_places=0, default=0)),
                ('correctness_rating', models.DecimalField(max_digits=3, decimal_places=0, default=0)),
                ('usefulness_rating', models.DecimalField(max_digits=3, decimal_places=0, default=0)),
                ('author', models.ForeignKey(to='scipost.Contributor')),
                ('in_reply_to_comment', models.ForeignKey(blank=True, null=True, to='scipost.Comment')),
                ('in_reply_to_report', models.ForeignKey(blank=True, null=True, to='scipost.Report')),
            ],
        ),
        migrations.CreateModel(
            name='AuthorReplyRating',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('clarity', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('correctness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('usefulness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('rater', models.ForeignKey(to='scipost.Contributor')),
                ('reply', models.ForeignKey(to='scipost.AuthorReply')),
            ],
        ),
    ]
