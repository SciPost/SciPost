# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0004_auto_20151203_0922'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='author',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='commentary',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='in_reply_to',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='submission',
        ),
        migrations.AlterField(
            model_name='authorreply',
            name='in_reply_to_comment',
            field=models.ForeignKey(null=True, to='comments.Comment', blank=True),
        ),
        migrations.AlterField(
            model_name='commentrating',
            name='comment',
            field=models.ForeignKey(to='comments.Comment'),
        ),
        migrations.DeleteModel(
            name='Comment',
        ),
    ]
