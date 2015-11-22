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
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('status', models.SmallIntegerField(default=0)),
                ('comment_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('correctness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('usefulness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
            ],
        ),
        migrations.CreateModel(
            name='Commentary',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
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
                ('clarity_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('correctness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('usefulness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('latest_activity', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='CommentaryRating',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('clarity', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('correctness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('usefulness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('commentary', models.ForeignKey(to='scipost.Commentary')),
            ],
        ),
        migrations.CreateModel(
            name='CommentRating',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('clarity', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('correctness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('usefulness', models.PositiveSmallIntegerField(verbose_name=((100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')))),
                ('comment', models.ForeignKey(to='scipost.Comment')),
            ],
        ),
        migrations.CreateModel(
            name='Contributor',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('rank', models.SmallIntegerField(default=0)),
                ('title', models.CharField(choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs')], max_length=4)),
                ('affiliation', models.CharField(max_length=300, verbose_name='affiliation')),
                ('address', models.CharField(blank=True, max_length=1000, verbose_name='address')),
                ('personalwebpage', models.URLField(blank=True, verbose_name='personal web page')),
                ('nr_reports', models.PositiveSmallIntegerField(default=0)),
                ('report_clarity_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('report_correctness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('report_usefulness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('nr_comments', models.PositiveSmallIntegerField(default=0)),
                ('comment_clarity_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('comment_correctness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('comment_usefulness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('status', models.SmallIntegerField(default=0)),
                ('strengths', models.TextField()),
                ('weaknesses', models.TextField()),
                ('report', models.TextField()),
                ('requested_changes', models.TextField()),
                ('recommendation', models.SmallIntegerField(choices=[(1, 'Publish as Tier I'), (2, 'Publish as Tier II'), (3, 'Publish as Tier III'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')])),
                ('date_invited', models.DateTimeField(blank=True, null=True, verbose_name='date invited')),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('correctness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('usefulness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('author', models.ForeignKey(to='scipost.Contributor')),
                ('invited_by', models.ForeignKey(related_name='invited_by', to='scipost.Contributor', blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReportRating',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
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
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('vetted', models.BooleanField(default=False)),
                ('submitted_to_journal', models.CharField(choices=[('Phys:Lett', 'Physics Letters'), ('Phys:Rev', 'Physics Reviews'), ('Phys:Lect', 'Physics Lecture Notes'), ('Phys:AMO', 'Physics AMO'), ('Phys:CM', 'Physics CM'), ('Phys:HEP', 'Physics HEP'), ('Phys:MP', 'Physics Math'), ('Phys:SP', 'Physics SP')], max_length=10)),
                ('status', models.SmallIntegerField(choices=[(0, 'unassigned'), (1, 'editor in charge assigned'), (2, 'under review'), (3, 'reviewed, peer checking period'), (4, 'reviewed, peer checked, editorial decision pending'), (5, 'editorial decision')])),
                ('open_for_reporting', models.BooleanField(default=True)),
                ('open_for_commenting', models.BooleanField(default=True)),
                ('title', models.CharField(max_length=300)),
                ('author_list', models.CharField(max_length=1000)),
                ('abstract', models.TextField()),
                ('arxiv_link', models.URLField(verbose_name='arXiv link (including version nr)')),
                ('submission_date', models.DateField(verbose_name='date of original publication')),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('correctness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('usefulness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('latest_activity', models.DateTimeField(default=django.utils.timezone.now)),
                ('editor_in_charge', models.ForeignKey(related_name='editor_in_charge', to='scipost.Contributor', blank=True, null=True)),
                ('submitted_by', models.ForeignKey(to='scipost.Contributor')),
            ],
        ),
        migrations.CreateModel(
            name='SubmissionRating',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
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
            field=models.ForeignKey(to='scipost.Contributor', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='comment',
            name='commentary',
            field=models.ForeignKey(to='scipost.Commentary', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='in_reply_to',
            field=models.ForeignKey(to='scipost.Comment', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='submission',
            field=models.ForeignKey(to='scipost.Submission', blank=True, null=True),
        ),
    ]
