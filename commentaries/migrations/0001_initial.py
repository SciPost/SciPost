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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
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
                ('clarity_rating', models.DecimalField(decimal_places=0, max_digits=3, default=0)),
                ('correctness_rating', models.DecimalField(decimal_places=0, max_digits=3, default=0)),
                ('usefulness_rating', models.DecimalField(decimal_places=0, max_digits=3, default=0)),
                ('latest_activity', models.DateTimeField(default=django.utils.timezone.now)),
                ('vetted_by', models.ForeignKey(blank=True, null=True, to='contributors.Contributor')),
            ],
        ),
    ]
