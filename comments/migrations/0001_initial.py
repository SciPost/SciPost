# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributors', '0001_initial'),
        ('submissions', '0001_initial'),
        ('reports', '0001_initial'),
        ('commentaries', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorReply',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('status', models.SmallIntegerField(default=0)),
                ('reply_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_relevance_ratings', models.IntegerField(default=0)),
                ('relevance_rating', models.DecimalField(max_digits=3, default=0, null=True, decimal_places=0)),
                ('nr_importance_ratings', models.IntegerField(default=0)),
                ('importance_rating', models.DecimalField(max_digits=3, default=0, null=True, decimal_places=0)),
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(max_digits=3, default=0, null=True, decimal_places=0)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(max_digits=3, default=0, null=True, decimal_places=0)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(max_digits=3, default=0, null=True, decimal_places=0)),
                ('author', models.ForeignKey(to='contributors.Contributor')),
                ('commentary', models.ForeignKey(null=True, to='commentaries.Commentary', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('status', models.SmallIntegerField(default=0)),
                ('comment_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_relevance_ratings', models.IntegerField(default=0)),
                ('relevance_rating', models.DecimalField(max_digits=3, default=0, null=True, decimal_places=0)),
                ('nr_importance_ratings', models.IntegerField(default=0)),
                ('importance_rating', models.DecimalField(max_digits=3, default=0, null=True, decimal_places=0)),
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(max_digits=3, default=0, null=True, decimal_places=0)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(max_digits=3, default=0, null=True, decimal_places=0)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(max_digits=3, default=0, null=True, decimal_places=0)),
                ('author', models.ForeignKey(to='contributors.Contributor')),
                ('commentary', models.ForeignKey(null=True, to='commentaries.Commentary', blank=True)),
                ('in_reply_to', models.ForeignKey(null=True, to='comments.Comment', blank=True)),
                ('submission', models.ForeignKey(null=True, to='submissions.Submission', blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='authorreply',
            name='in_reply_to_comment',
            field=models.ForeignKey(null=True, to='comments.Comment', blank=True),
        ),
        migrations.AddField(
            model_name='authorreply',
            name='in_reply_to_report',
            field=models.ForeignKey(null=True, to='reports.Report', blank=True),
        ),
        migrations.AddField(
            model_name='authorreply',
            name='submission',
            field=models.ForeignKey(null=True, to='submissions.Submission', blank=True),
        ),
    ]
