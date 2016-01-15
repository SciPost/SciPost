# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0001_initial'),
        ('commentaries', '0001_initial'),
        ('comments', '0001_initial'),
        ('scipost', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorReplyRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relevance', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('importance', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('clarity', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('validity', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('rigour', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clarity', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('validity', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('rigour', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('originality', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('significance', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relevance', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('importance', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('clarity', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('validity', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('rigour', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relevance', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('importance', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('clarity', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('validity', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('rigour', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('rater', models.ForeignKey(to='scipost.Contributor')),
                ('report', models.ForeignKey(to='submissions.Report')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubmissionRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clarity', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('validity', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('rigour', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('originality', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('significance', models.PositiveSmallIntegerField(default=0, verbose_name=((101, '-'), (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')), null=True)),
                ('rater', models.ForeignKey(to='scipost.Contributor')),
                ('submission', models.ForeignKey(to='submissions.Submission')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
