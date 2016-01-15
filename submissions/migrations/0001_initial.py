# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.SmallIntegerField(default=0)),
                ('qualification', models.PositiveSmallIntegerField(default=0)),
                ('strengths', models.TextField()),
                ('weaknesses', models.TextField()),
                ('report', models.TextField()),
                ('requested_changes', models.TextField()),
                ('recommendation', models.SmallIntegerField(choices=[(1, 'Publish as Tier I (top 10% of papers in this journal)'), (2, 'Publish as Tier II (top 50% of papers in this journal)'), (3, 'Publish as Tier III (meets the criteria of this journal)'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')])),
                ('date_invited', models.DateTimeField(blank=True, null=True, verbose_name='date invited')),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_relevance_ratings', models.IntegerField(default=0)),
                ('relevance_rating', models.DecimalField(default=0, max_digits=3, null=True, decimal_places=0)),
                ('nr_importance_ratings', models.IntegerField(default=0)),
                ('importance_rating', models.DecimalField(default=0, max_digits=3, null=True, decimal_places=0)),
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(default=0, max_digits=3, null=True, decimal_places=0)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(default=0, max_digits=3, null=True, decimal_places=0)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(default=0, max_digits=3, null=True, decimal_places=0)),
                ('author', models.ForeignKey(to='scipost.Contributor')),
                ('invited_by', models.ForeignKey(blank=True, to='scipost.Contributor', related_name='invited_by', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vetted', models.BooleanField(default=False)),
                ('submitted_to_journal', models.CharField(choices=[('SciPost Physics Select', 'SciPost Physics Select'), ('SciPost Physics Letters', 'SciPost Physics Letters'), ('SciPost Physics X', 'SciPost Physics X (cross-division)'), ('SciPost Physics', 'SciPost Physics (Experimental, Theoretical and Computational)'), ('SciPost Physics Lecture Notes', 'SciPost Physics Lecture Notes')], max_length=30)),
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
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(default=0, max_digits=3, null=True, decimal_places=0)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(default=0, max_digits=3, null=True, decimal_places=0)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(default=0, max_digits=3, null=True, decimal_places=0)),
                ('nr_originality_ratings', models.IntegerField(default=0)),
                ('originality_rating', models.DecimalField(default=0, max_digits=3, null=True, decimal_places=0)),
                ('nr_significance_ratings', models.IntegerField(default=0)),
                ('significance_rating', models.DecimalField(default=0, max_digits=3, null=True, decimal_places=0)),
                ('latest_activity', models.DateTimeField(default=django.utils.timezone.now)),
                ('authors', models.ManyToManyField(blank=True, related_name='authors_sub', to='scipost.Contributor')),
                ('editor_in_charge', models.ForeignKey(blank=True, to='scipost.Contributor', related_name='editor_in_charge', null=True)),
                ('submitted_by', models.ForeignKey(to='scipost.Contributor')),
            ],
        ),
        migrations.AddField(
            model_name='report',
            name='submission',
            field=models.ForeignKey(to='submissions.Submission'),
        ),
    ]
