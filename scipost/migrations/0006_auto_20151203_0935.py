# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0005_auto_20151203_0928'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authorreplyrating',
            name='rater',
        ),
        migrations.RemoveField(
            model_name='authorreplyrating',
            name='reply',
        ),
        migrations.RemoveField(
            model_name='commentaryrating',
            name='commentary',
        ),
        migrations.RemoveField(
            model_name='commentaryrating',
            name='rater',
        ),
        migrations.RemoveField(
            model_name='commentrating',
            name='comment',
        ),
        migrations.RemoveField(
            model_name='commentrating',
            name='rater',
        ),
        migrations.RemoveField(
            model_name='reportrating',
            name='rater',
        ),
        migrations.RemoveField(
            model_name='reportrating',
            name='report',
        ),
        migrations.RemoveField(
            model_name='submissionrating',
            name='rater',
        ),
        migrations.RemoveField(
            model_name='submissionrating',
            name='submission',
        ),
        migrations.DeleteModel(
            name='AuthorReplyRating',
        ),
        migrations.DeleteModel(
            name='CommentaryRating',
        ),
        migrations.DeleteModel(
            name='CommentRating',
        ),
        migrations.DeleteModel(
            name='ReportRating',
        ),
        migrations.DeleteModel(
            name='SubmissionRating',
        ),
    ]
