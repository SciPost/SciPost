# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commentaries', '0001_initial'),
        ('scipost', '0001_initial'),
        ('submissions', '0001_initial'),
        ('comments', '0001_initial'),
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorReplyRating',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('relevance', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('importance', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('clarity', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('validity', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('rigour', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('authorreply', models.ForeignKey(to='comments.AuthorReply')),
                ('rater', models.ForeignKey(to='scipost.Contributor')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CommentaryRating',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('clarity', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('validity', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('rigour', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('originality', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('significance', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('commentary', models.ForeignKey(to='commentaries.Commentary')),
                ('rater', models.ForeignKey(to='scipost.Contributor')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CommentRating',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('relevance', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('importance', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('clarity', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('validity', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('rigour', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('comment', models.ForeignKey(to='comments.Comment')),
                ('rater', models.ForeignKey(to='scipost.Contributor')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReportRating',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('relevance', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('importance', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('clarity', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('validity', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('rigour', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('rater', models.ForeignKey(to='scipost.Contributor')),
                ('report', models.ForeignKey(to='reports.Report')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubmissionRating',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('clarity', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('validity', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('rigour', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('originality', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('significance', models.PositiveSmallIntegerField(null=True, default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('rater', models.ForeignKey(to='scipost.Contributor')),
                ('submission', models.ForeignKey(to='submissions.Submission')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
