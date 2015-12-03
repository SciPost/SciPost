# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ratings', '0002_auto_20151203_0938'),
        ('scipost', '0006_auto_20151203_0935'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='report',
            name='author',
        ),
        migrations.RemoveField(
            model_name='report',
            name='invited_by',
        ),
        migrations.RemoveField(
            model_name='report',
            name='submission',
        ),
        migrations.AlterField(
            model_name='authorreply',
            name='in_reply_to_report',
            field=models.ForeignKey(to='reports.Report', blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='Report',
        ),
    ]
