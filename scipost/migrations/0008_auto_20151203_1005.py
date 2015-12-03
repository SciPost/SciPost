# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ratings', '0003_auto_20151203_1005'),
        ('scipost', '0007_auto_20151203_0938'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authorreply',
            name='author',
        ),
        migrations.RemoveField(
            model_name='authorreply',
            name='commentary',
        ),
        migrations.RemoveField(
            model_name='authorreply',
            name='in_reply_to_comment',
        ),
        migrations.RemoveField(
            model_name='authorreply',
            name='in_reply_to_report',
        ),
        migrations.RemoveField(
            model_name='authorreply',
            name='submission',
        ),
        migrations.DeleteModel(
            name='AuthorReply',
        ),
    ]
