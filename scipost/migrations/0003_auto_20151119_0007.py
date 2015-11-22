# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0002_authorreply_authorreplyrating'),
    ]

    operations = [
        migrations.AddField(
            model_name='authorreply',
            name='commentary',
            field=models.ForeignKey(blank=True, null=True, to='scipost.Commentary'),
        ),
        migrations.AddField(
            model_name='authorreply',
            name='submission',
            field=models.ForeignKey(blank=True, null=True, to='scipost.Submission'),
        ),
    ]
