# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-01-14 04:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0018_contributor_duplicate_of'),
        ('colleges', '0011_auto_20190113_1942'),
    ]

    operations = [
        migrations.AddField(
            model_name='potentialfellowship',
            name='elected',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='potentialfellowship',
            name='in_abstain',
            field=models.ManyToManyField(blank=True, related_name='in_abstain_with_election', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='potentialfellowship',
            name='in_agreement',
            field=models.ManyToManyField(blank=True, related_name='in_agreement_with_election', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='potentialfellowship',
            name='in_disagreement',
            field=models.ManyToManyField(blank=True, related_name='in_disagreement_with_election', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='potentialfellowship',
            name='voting_deadline',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='voting deadline'),
        ),
        migrations.AlterField(
            model_name='potentialfellowship',
            name='status',
            field=models.CharField(choices=[('identified', 'Identified as potential Fellow'), ('nominated', 'Nominated for Fellowship'), ('electionvoteongoing', 'Election vote ongoing'), ('elected', 'Elected by the College'), ('notelected', 'Not elected by the College'), ('invited', 'Invited to become Fellow'), ('reinvited', 'Reinvited after initial invitation'), ('multiplyreinvited', 'Multiply reinvited'), ('declined', 'Declined the invitation'), ('unresponsive', 'Marked as unresponsive'), ('retired', 'Retired'), ('deceased', 'Deceased'), ('interested', 'Marked as interested, Fellowship being set up'), ('registered', 'Registered as Contributor'), ('activeincollege', 'Currently active in a College'), ('emeritus', 'SciPost Emeritus')], default='identified', max_length=32),
        ),
    ]
