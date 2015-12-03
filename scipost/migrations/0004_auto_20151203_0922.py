# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0003_auto_20151202_1843'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='editor_in_charge',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='submitted_by',
        ),
        migrations.AlterField(
            model_name='authorreply',
            name='submission',
            field=models.ForeignKey(blank=True, to='submissions.Submission', null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='submission',
            field=models.ForeignKey(blank=True, to='submissions.Submission', null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='submission',
            field=models.ForeignKey(to='submissions.Submission'),
        ),
        migrations.AlterField(
            model_name='submissionrating',
            name='submission',
            field=models.ForeignKey(to='submissions.Submission'),
        ),
        migrations.DeleteModel(
            name='Submission',
        ),
    ]
