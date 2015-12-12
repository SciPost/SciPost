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
            name='Commentary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
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
                ('authors', models.ManyToManyField(related_name='authors_com', blank=True, null=True, to='contributors.Contributor')),
                ('vetted_by', models.ForeignKey(null=True, to='contributors.Contributor', blank=True)),
            ],
        ),
    ]
