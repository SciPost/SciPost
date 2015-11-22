# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0003_auto_20151119_0007'),
    ]

    operations = [
        migrations.AddField(
            model_name='contributor',
            name='orcid_id',
            field=models.CharField(blank=True, max_length=20, default='', verbose_name='ORCID id', null=True),
        ),
    ]
