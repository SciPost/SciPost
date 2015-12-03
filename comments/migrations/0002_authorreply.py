# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributors', '0001_initial'),
        ('reports', '0001_initial'),
        ('commentaries', '0001_initial'),
        ('submissions', '0001_initial'),
        ('comments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorReply',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('status', models.SmallIntegerField(default=0)),
                ('reply_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('correctness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('usefulness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('author', models.ForeignKey(to='contributors.Contributor')),
                ('commentary', models.ForeignKey(blank=True, null=True, to='commentaries.Commentary')),
                ('in_reply_to_comment', models.ForeignKey(blank=True, null=True, to='comments.Comment')),
                ('in_reply_to_report', models.ForeignKey(blank=True, null=True, to='reports.Report')),
                ('submission', models.ForeignKey(blank=True, null=True, to='submissions.Submission')),
            ],
        ),
    ]
