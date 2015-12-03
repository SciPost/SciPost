# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributors', '0001_initial'),
        ('submissions', '0001_initial'),
        ('commentaries', '0001_initial'),
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
                ('clarity_rating', models.DecimalField(decimal_places=0, max_digits=3, default=0)),
                ('correctness_rating', models.DecimalField(decimal_places=0, max_digits=3, default=0)),
                ('usefulness_rating', models.DecimalField(decimal_places=0, max_digits=3, default=0)),
                ('author', models.ForeignKey(to='contributors.Contributor')),
                ('commentary', models.ForeignKey(null=True, to='commentaries.Commentary', blank=True)),
                ('in_reply_to', models.ForeignKey(null=True, to='comments.Comment', blank=True)),
                ('submission', models.ForeignKey(null=True, to='submissions.Submission', blank=True)),
            ],
        ),
    ]
