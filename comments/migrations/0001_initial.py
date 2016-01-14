# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0001_initial'),
        ('submissions', '0001_initial'),
        ('reports', '0001_initial'),
        ('commentaries', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorReply',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('status', models.SmallIntegerField(default=0)),
                ('reply_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_relevance_ratings', models.IntegerField(default=0)),
                ('relevance_rating', models.DecimalField(decimal_places=0, max_digits=3, null=True, default=0)),
                ('nr_importance_ratings', models.IntegerField(default=0)),
                ('importance_rating', models.DecimalField(decimal_places=0, max_digits=3, null=True, default=0)),
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(decimal_places=0, max_digits=3, null=True, default=0)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(decimal_places=0, max_digits=3, null=True, default=0)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(decimal_places=0, max_digits=3, null=True, default=0)),
                ('author', models.ForeignKey(to='scipost.Contributor')),
                ('commentary', models.ForeignKey(null=True, blank=True, to='commentaries.Commentary')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('status', models.SmallIntegerField(default=0)),
                ('is_rem', models.BooleanField(verbose_name='remark', default=False)),
                ('is_que', models.BooleanField(verbose_name='question', default=False)),
                ('is_ans', models.BooleanField(verbose_name='answer to question', default=False)),
                ('is_obj', models.BooleanField(verbose_name='objection', default=False)),
                ('is_rep', models.BooleanField(verbose_name='reply to objection', default=False)),
                ('is_val', models.BooleanField(verbose_name='validation or rederivation', default=False)),
                ('is_lit', models.BooleanField(verbose_name='pointer to related literature', default=False)),
                ('is_sug', models.BooleanField(verbose_name='suggestion for further work', default=False)),
                ('comment_text', models.TextField()),
                ('date_submitted', models.DateTimeField(verbose_name='date submitted')),
                ('nr_relevance_ratings', models.IntegerField(default=0)),
                ('relevance_rating', models.DecimalField(decimal_places=0, max_digits=3, null=True, default=0)),
                ('nr_importance_ratings', models.IntegerField(default=0)),
                ('importance_rating', models.DecimalField(decimal_places=0, max_digits=3, null=True, default=0)),
                ('nr_clarity_ratings', models.IntegerField(default=0)),
                ('clarity_rating', models.DecimalField(decimal_places=0, max_digits=3, null=True, default=0)),
                ('nr_validity_ratings', models.IntegerField(default=0)),
                ('validity_rating', models.DecimalField(decimal_places=0, max_digits=3, null=True, default=0)),
                ('nr_rigour_ratings', models.IntegerField(default=0)),
                ('rigour_rating', models.DecimalField(decimal_places=0, max_digits=3, null=True, default=0)),
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
