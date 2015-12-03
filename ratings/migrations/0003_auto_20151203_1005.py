# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ratings', '0002_auto_20151203_0938'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorreplyrating',
            name='reply',
            field=models.ForeignKey(to='comments.AuthorReply'),
        ),
    ]
