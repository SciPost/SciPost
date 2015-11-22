# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0004_contributor_orcid_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='submitted_to_journal',
            field=models.CharField(max_length=10, choices=[('Phys:Lett', 'SciPost Physics Letters'), ('Phys', 'SciPost Physics')]),
        ),
    ]
