# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0001_initial'),
        ('contributors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('status', models.SmallIntegerField(default=0)),
                ('qualification', models.PositiveSmallIntegerField(default=0)),
                ('strengths', models.TextField()),
                ('weaknesses', models.TextField()),
                ('report', models.TextField()),
                ('requested_changes', models.TextField()),
                ('recommendation', models.SmallIntegerField(choices=[(1, 'Publish as Tier I (top 10% of papers in this journal)'), (2, 'Publish as Tier II (top 50% of papers in this journal)'), (3, 'Publish as Tier III (meets the criteria of this journal)'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')])),
                ('date_invited', models.DateTimeField(verbose_name='date invited', blank=True, null=True)),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_relevance_ratings', models.IntegerField(default=0)),
                ('relevance_rating', models.DecimalField(default=0, decimal_places=0, null=True, max_digits=3)),
                ('nr_importance_ratings', models.IntegerField(default=0)),
                ('importance_rating', models.DecimalField(default=0, decimal_places=0, null=True, max_digits=3)),
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(default=0, decimal_places=0, null=True, max_digits=3)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(default=0, decimal_places=0, null=True, max_digits=3)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(default=0, decimal_places=0, null=True, max_digits=3)),
                ('author', models.ForeignKey(to='contributors.Contributor')),
                ('invited_by', models.ForeignKey(null=True, to='contributors.Contributor', blank=True, related_name='invited_by')),
                ('submission', models.ForeignKey(to='submissions.Submission')),
            ],
        ),
    ]
