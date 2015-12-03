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
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('status', models.SmallIntegerField(default=0)),
                ('qualification', models.PositiveSmallIntegerField(default=0)),
                ('strengths', models.TextField()),
                ('weaknesses', models.TextField()),
                ('report', models.TextField()),
                ('requested_changes', models.TextField()),
                ('recommendation', models.SmallIntegerField(choices=[(1, 'Publish as Tier I (top 10% of papers in this journal)'), (2, 'Publish as Tier II (top 50% of papers in this journal)'), (3, 'Publish as Tier III (meets the criteria of this journal)'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')])),
                ('date_invited', models.DateTimeField(null=True, blank=True, verbose_name='date invited')),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('correctness_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('usefulness_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('author', models.ForeignKey(to='contributors.Contributor')),
                ('invited_by', models.ForeignKey(related_name='invited_by', blank=True, to='contributors.Contributor', null=True)),
                ('submission', models.ForeignKey(to='submissions.Submission')),
            ],
        ),
    ]
