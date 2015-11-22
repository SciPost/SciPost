# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0013_auto_20151120_0258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='recommendation',
            field=models.SmallIntegerField(choices=[(1, 'Publish as Tier I (top 10% of papers in this journal)'), (2, 'Publish as Tier II (top 50% of papers in this journal)'), (3, 'Publish as Tier III (meets the criteria of this journal)'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')]),
        ),
    ]
