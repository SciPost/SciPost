# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-17 19:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Commentary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vetted', models.BooleanField(default=False)),
                ('type', models.CharField(choices=[('published', 'published paper'), ('preprint', 'arXiv preprint (at least 8 weeks old)')], max_length=9)),
                ('discipline', models.CharField(choices=[('physics', 'Physics')], default='physics', max_length=20)),
                ('domain', models.CharField(choices=[('E', 'Experimental'), ('T', 'Theoretical'), ('C', 'Computational'), ('ET', 'Exp. & Theor.'), ('EC', 'Exp. & Comp.'), ('TC', 'Theor. & Comp.'), ('ETC', 'Exp., Theor. & Comp.')], default='E', max_length=3)),
                ('specialization', models.CharField(choices=[('A', 'Atomic, Molecular and Optical Physics'), ('B', 'Biophysics'), ('C', 'Condensed Matter Physics'), ('F', 'Fluid Dynamics'), ('G', 'Gravitation, Cosmology and Astroparticle Physics'), ('H', 'High-Energy Physics'), ('M', 'Mathematical Physics'), ('N', 'Nuclear Physics'), ('Q', 'Quantum Statistical Mechanics'), ('S', 'Statistical and Soft Matter Physics')], default='A', max_length=1)),
                ('open_for_commenting', models.BooleanField(default=True)),
                ('pub_title', models.CharField(max_length=300, verbose_name='title')),
                ('arxiv_link', models.URLField(blank=True, verbose_name='arXiv link (including version nr)')),
                ('pub_DOI_link', models.URLField(blank=True, verbose_name='DOI link to the original publication')),
                ('author_list', models.CharField(max_length=1000)),
                ('pub_date', models.DateField(verbose_name='date of original publication')),
                ('pub_abstract', models.TextField(verbose_name='abstract')),
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(decimal_places=0, default=101, max_digits=3, null=True)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(decimal_places=0, default=101, max_digits=3, null=True)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(decimal_places=0, default=101, max_digits=3, null=True)),
                ('nr_originality_ratings', models.IntegerField(default=0)),
                ('originality_rating', models.DecimalField(decimal_places=0, default=101, max_digits=3, null=True)),
                ('nr_significance_ratings', models.IntegerField(default=0)),
                ('significance_rating', models.DecimalField(decimal_places=0, default=101, max_digits=3, null=True)),
                ('latest_activity', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
