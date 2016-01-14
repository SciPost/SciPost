# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commentaries', '0001_initial'),
        ('scipost', '0001_initial'),
        ('submissions', '0001_initial'),
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorReply',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('status', models.SmallIntegerField(default=0)),
                ('reply_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_relevance_ratings', models.IntegerField(default=0)),
                ('relevance_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_importance_ratings', models.IntegerField(default=0)),
                ('importance_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('author', models.ForeignKey(to='scipost.Contributor')),
                ('commentary', models.ForeignKey(null=True, blank=True, to='commentaries.Commentary')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('status', models.SmallIntegerField(default=0)),
                ('is_rem', models.BooleanField(default=False, verbose_name='remark')),
                ('is_que', models.BooleanField(default=False, verbose_name='question')),
                ('is_ans', models.BooleanField(default=False, verbose_name='answer to question')),
                ('is_obj', models.BooleanField(default=False, verbose_name='objection')),
                ('is_rep', models.BooleanField(default=False, verbose_name='reply to objection')),
                ('is_val', models.BooleanField(default=False, verbose_name='validation or rederivation')),
                ('is_lit', models.BooleanField(default=False, verbose_name='pointer to related literature')),
                ('is_sug', models.BooleanField(default=False, verbose_name='suggestion for further work')),
                ('comment_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_relevance_ratings', models.IntegerField(default=0)),
                ('relevance_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_importance_ratings', models.IntegerField(default=0)),
                ('importance_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(null=True, decimal_places=0, default=0, max_digits=3)),
                ('author', models.ForeignKey(to='scipost.Contributor')),
                ('commentary', models.ForeignKey(null=True, blank=True, to='commentaries.Commentary')),
                ('in_reply_to', models.ForeignKey(null=True, blank=True, to='comments.Comment')),
                ('submission', models.ForeignKey(null=True, blank=True, to='submissions.Submission')),
            ],
        ),
        migrations.AddField(
            model_name='authorreply',
            name='in_reply_to_comment',
            field=models.ForeignKey(null=True, blank=True, to='comments.Comment'),
        ),
        migrations.AddField(
            model_name='authorreply',
            name='in_reply_to_report',
            field=models.ForeignKey(null=True, blank=True, to='reports.Report'),
        ),
        migrations.AddField(
            model_name='authorreply',
            name='submission',
            field=models.ForeignKey(null=True, blank=True, to='submissions.Submission'),
        ),
    ]
