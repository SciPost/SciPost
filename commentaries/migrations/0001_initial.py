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
            name='Commentary',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('vetted', models.BooleanField(default=False)),
                ('type', models.CharField(max_length=9)),
                ('open_for_commenting', models.BooleanField(default=True)),
                ('pub_title', models.CharField(max_length=300)),
                ('arxiv_link', models.URLField(verbose_name='arXiv link (including version nr)')),
                ('pub_DOI_link', models.URLField(verbose_name='DOI link to the original publication')),
                ('author_list', models.CharField(max_length=1000)),
                ('pub_date', models.DateField(verbose_name='date of original publication')),
                ('pub_abstract', models.TextField()),
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_originality_ratings', models.IntegerField(default=0)),
                ('originality_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_significance_ratings', models.IntegerField(default=0)),
                ('significance_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('latest_activity', models.DateTimeField(default=django.utils.timezone.now)),
                ('authors', models.ManyToManyField(related_name='authors_com', blank=True, to='scipost.Contributor')),
                ('requested_by', models.ForeignKey(null=True, related_name='requested_by', blank=True, to='scipost.Contributor')),
                ('vetted_by', models.ForeignKey(null=True, blank=True, to='scipost.Contributor')),
            ],
        ),
    ]
