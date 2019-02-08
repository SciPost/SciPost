# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-01-13 18:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0010_auto_20180917_2117'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='potentialfellowship',
            options={'ordering': ['profile__last_name']},
        ),
        migrations.AlterField(
            model_name='potentialfellowship',
            name='status',
            field=models.CharField(choices=[('identified', 'Identified as potential Fellow'), ('nominated', 'Nominated for Fellowship'), ('elected', 'Elected by the College'), ('notelected', 'Not elected by the College'), ('invited', 'Invited to become Fellow'), ('reinvited', 'Reinvited after initial invitation'), ('multiplyreinvited', 'Multiply reinvited'), ('declined', 'Declined the invitation'), ('unresponsive', 'Marked as unresponsive'), ('retired', 'Retired'), ('deceased', 'Deceased'), ('interested', 'Marked as interested, Fellowship being set up'), ('registered', 'Registered as Contributor'), ('activeincollege', 'Currently active in a College'), ('emeritus', 'SciPost Emeritus')], default='identified', max_length=32),
        ),
    ]
