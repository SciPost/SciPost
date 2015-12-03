# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0002_auto_20151202_1831'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commentary',
            name='vetted_by',
        ),
        migrations.AlterField(
            model_name='authorreply',
            name='commentary',
            field=models.ForeignKey(blank=True, null=True, to='commentaries.Commentary'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='commentary',
            field=models.ForeignKey(blank=True, null=True, to='commentaries.Commentary'),
        ),
        migrations.AlterField(
            model_name='commentaryrating',
            name='commentary',
            field=models.ForeignKey(to='commentaries.Commentary'),
        ),
        migrations.DeleteModel(
            name='Commentary',
        ),
    ]
