# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorReply',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('status', models.SmallIntegerField(default=0)),
                ('reply_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('correctness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('usefulness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
            ],
        ),
        migrations.CreateModel(
            name='AuthorReplyRating',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('clarity', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('correctness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('usefulness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('status', models.SmallIntegerField(default=0)),
                ('comment_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('correctness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('usefulness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
            ],
        ),
        migrations.CreateModel(
            name='Commentary',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('vetted', models.BooleanField(default=False)),
                ('type', models.CharField(max_length=9)),
                ('open_for_commenting', models.BooleanField(default=True)),
                ('pub_title', models.CharField(max_length=300)),
                ('arxiv_link', models.URLField(verbose_name='arXiv link (including version nr)')),
                ('pub_DOI_link', models.URLField(verbose_name='DOI link to the original publication')),
                ('author_list', models.CharField(max_length=1000)),
                ('pub_date', models.DateField(verbose_name='date of original publication')),
                ('pub_abstract', models.TextField()),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('correctness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('usefulness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('latest_activity', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='CommentaryRating',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('clarity', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('correctness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('usefulness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('commentary', models.ForeignKey(to='scipost.Commentary')),
            ],
        ),
        migrations.CreateModel(
            name='CommentRating',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('clarity', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('correctness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('usefulness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('comment', models.ForeignKey(to='scipost.Comment')),
            ],
        ),
        migrations.CreateModel(
            name='Contributor',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('rank', models.SmallIntegerField(default=0, choices=[(0, 'newly registered'), (1, 'normal user'), (2, 'SciPost Commentary Editor'), (3, 'SciPost Journal Editor'), (4, 'SciPost Journal Editor-in-chief'), (5, 'SciPost Lead Editor'), (-1, 'not a professional scientist'), (-2, 'other account already exists'), (-3, 'barred from SciPost'), (-4, 'account disabled')])),
                ('title', models.CharField(choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs')], max_length=4)),
                ('orcid_id', models.CharField(default='', verbose_name='ORCID id', max_length=20, null=True, blank=True)),
                ('affiliation', models.CharField(verbose_name='affiliation', max_length=300)),
                ('address', models.CharField(verbose_name='address', max_length=1000, blank=True)),
                ('personalwebpage', models.URLField(verbose_name='personal web page', blank=True)),
                ('nr_reports', models.PositiveSmallIntegerField(default=0)),
                ('report_clarity_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('report_correctness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('report_usefulness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('nr_comments', models.PositiveSmallIntegerField(default=0)),
                ('comment_clarity_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('comment_correctness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('comment_usefulness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('status', models.SmallIntegerField(default=0)),
                ('qualification', models.PositiveSmallIntegerField(default=0)),
                ('strengths', models.TextField()),
                ('weaknesses', models.TextField()),
                ('report', models.TextField()),
                ('requested_changes', models.TextField()),
                ('recommendation', models.SmallIntegerField(choices=[(1, 'Publish as Tier I (top 10% of papers in this journal)'), (2, 'Publish as Tier II (top 50% of papers in this journal)'), (3, 'Publish as Tier III (meets the criteria of this journal)'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')])),
                ('date_invited', models.DateTimeField(verbose_name='date invited', null=True, blank=True)),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('correctness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('usefulness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('author', models.ForeignKey(to='scipost.Contributor')),
                ('invited_by', models.ForeignKey(related_name='invited_by', to='scipost.Contributor', null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReportRating',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('clarity', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('correctness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('usefulness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('rater', models.ForeignKey(to='scipost.Contributor')),
                ('report', models.ForeignKey(to='scipost.Report')),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('vetted', models.BooleanField(default=False)),
                ('submitted_to_journal', models.CharField(choices=[('SciPost Physics Select', 'SciPost Physics Select'), ('SciPost Physics Letters', 'SciPost Physics Letters'), ('SciPost Physics X', 'SciPost Physics X (cross-division)'), ('SciPost Physics', 'SciPost Physics (Experimental, Theoretical and Computational)')], max_length=30)),
                ('domain', models.CharField(default='E', choices=[('E', 'Experimental'), ('T', 'Theoretical'), ('C', 'Computational')], max_length=1)),
                ('specialization', models.CharField(choices=[('A', 'Atomic, Molecular and Optical Physics'), ('B', 'Biophysics'), ('C', 'Condensed Matter Physics'), ('F', 'Fluid Dynamics'), ('G', 'Gravitation, Cosmology and Astroparticle Physics'), ('H', 'High-Energy Physics'), ('M', 'Mathematical Physics'), ('N', 'Nuclear Physics'), ('Q', 'Quantum Statistical Mechanics'), ('S', 'Statistical and Soft Matter Physics')], max_length=1)),
                ('status', models.SmallIntegerField(choices=[(0, 'unassigned'), (1, 'editor in charge assigned'), (2, 'under review'), (3, 'reviewed, peer checking period'), (4, 'reviewed, peer checked, editorial decision pending'), (5, 'editorial decision')])),
                ('open_for_reporting', models.BooleanField(default=True)),
                ('open_for_commenting', models.BooleanField(default=True)),
                ('title', models.CharField(max_length=300)),
                ('author_list', models.CharField(max_length=1000)),
                ('abstract', models.TextField()),
                ('arxiv_link', models.URLField(verbose_name='arXiv link (including version nr)')),
                ('submission_date', models.DateField(verbose_name='date of original publication')),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('correctness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('usefulness_rating', models.DecimalField(default=0, max_digits=3, decimal_places=0)),
                ('latest_activity', models.DateTimeField(default=django.utils.timezone.now)),
                ('editor_in_charge', models.ForeignKey(related_name='editor_in_charge', to='scipost.Contributor', null=True, blank=True)),
                ('submitted_by', models.ForeignKey(to='scipost.Contributor')),
            ],
        ),
        migrations.CreateModel(
            name='SubmissionRating',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('clarity', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('correctness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('usefulness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('rater', models.ForeignKey(to='scipost.Contributor')),
                ('submission', models.ForeignKey(to='scipost.Submission')),
            ],
        ),
        migrations.AddField(
            model_name='report',
            name='submission',
            field=models.ForeignKey(to='scipost.Submission'),
        ),
        migrations.AddField(
            model_name='commentrating',
            name='rater',
            field=models.ForeignKey(to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='commentaryrating',
            name='rater',
            field=models.ForeignKey(to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='commentary',
            name='vetted_by',
            field=models.ForeignKey(to='scipost.Contributor', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='comment',
            name='commentary',
            field=models.ForeignKey(to='scipost.Commentary', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='in_reply_to',
            field=models.ForeignKey(to='scipost.Comment', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='submission',
            field=models.ForeignKey(to='scipost.Submission', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='authorreplyrating',
            name='rater',
            field=models.ForeignKey(to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='authorreplyrating',
            name='reply',
            field=models.ForeignKey(to='scipost.AuthorReply'),
        ),
        migrations.AddField(
            model_name='authorreply',
            name='author',
            field=models.ForeignKey(to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='authorreply',
            name='commentary',
            field=models.ForeignKey(to='scipost.Commentary', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='authorreply',
            name='in_reply_to_comment',
            field=models.ForeignKey(to='scipost.Comment', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='authorreply',
            name='in_reply_to_report',
            field=models.ForeignKey(to='scipost.Report', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='authorreply',
            name='submission',
            field=models.ForeignKey(to='scipost.Submission', null=True, blank=True),
        ),
    ]
