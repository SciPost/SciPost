# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contributor',
            name='user',
        ),
        migrations.AlterField(
            model_name='authorreply',
            name='author',
            field=models.ForeignKey(to='contributors.Contributor'),
        ),
        migrations.AlterField(
            model_name='authorreplyrating',
            name='rater',
            field=models.ForeignKey(to='contributors.Contributor'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(to='contributors.Contributor'),
        ),
        migrations.AlterField(
            model_name='commentary',
            name='vetted_by',
            field=models.ForeignKey(to='contributors.Contributor', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='commentaryrating',
            name='rater',
            field=models.ForeignKey(to='contributors.Contributor'),
        ),
        migrations.AlterField(
            model_name='commentrating',
            name='rater',
            field=models.ForeignKey(to='contributors.Contributor'),
        ),
        migrations.AlterField(
            model_name='report',
            name='author',
            field=models.ForeignKey(to='contributors.Contributor'),
        ),
        migrations.AlterField(
            model_name='report',
            name='invited_by',
            field=models.ForeignKey(to='contributors.Contributor', blank=True, null=True, related_name='invited_by'),
        ),
        migrations.AlterField(
            model_name='reportrating',
            name='rater',
            field=models.ForeignKey(to='contributors.Contributor'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='editor_in_charge',
            field=models.ForeignKey(to='contributors.Contributor', blank=True, null=True, related_name='editor_in_charge'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='submitted_by',
            field=models.ForeignKey(to='contributors.Contributor'),
        ),
        migrations.AlterField(
            model_name='submissionrating',
            name='rater',
            field=models.ForeignKey(to='contributors.Contributor'),
        ),
        migrations.DeleteModel(
            name='Contributor',
        ),
    ]
