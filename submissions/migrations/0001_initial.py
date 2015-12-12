# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('contributors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
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
                ('clarity_rating', models.DecimalField(default=0, decimal_places=0, null=True, max_digits=3)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(default=0, decimal_places=0, null=True, max_digits=3)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(default=0, decimal_places=0, null=True, max_digits=3)),
                ('nr_originality_ratings', models.IntegerField(default=0)),
                ('originality_rating', models.DecimalField(default=0, decimal_places=0, null=True, max_digits=3)),
                ('nr_significance_ratings', models.IntegerField(default=0)),
                ('significance_rating', models.DecimalField(default=0, decimal_places=0, null=True, max_digits=3)),
                ('latest_activity', models.DateTimeField(default=django.utils.timezone.now)),
                ('authors', models.ManyToManyField(related_name='authors_sub', blank=True, null=True, to='contributors.Contributor')),
                ('editor_in_charge', models.ForeignKey(null=True, to='contributors.Contributor', blank=True, related_name='editor_in_charge')),
                ('submitted_by', models.ForeignKey(to='contributors.Contributor')),
            ],
        ),
    ]
