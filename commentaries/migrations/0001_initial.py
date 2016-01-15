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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
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
                ('authors', models.ManyToManyField(blank=True, related_name='authors_com', to='scipost.Contributor')),
                ('requested_by', models.ForeignKey(blank=True, to='scipost.Contributor', related_name='requested_by', null=True)),
                ('vetted_by', models.ForeignKey(blank=True, to='scipost.Contributor', null=True)),
            ],
        ),
    ]
