# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-08-13 12:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scipost', '0016_remark'),
        ('submissions', '0019_remove_submission_specialization'),
    ]

    operations = [
        migrations.AddField(
            model_name='eicrecommendation',
            name='eligible_to_vote',
            field=models.ManyToManyField(blank=True, related_name='eligible_to_vote', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='eicrecommendation',
            name='remarks_during_voting',
            field=models.ManyToManyField(blank=True, to='scipost.Remark'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='status',
            field=models.CharField(choices=[('unassigned', 'Unassigned, undergoing pre-screening'), ('assignment_failed', 'Failed to assign Editor-in-charge; manuscript rejected'), ('EICassigned', 'Editor-in-charge assigned, manuscript under review'), ('review_closed', 'Review period closed, editorial recommendation pending'), ('revision_requested', 'Editor-in-charge has requested revision'), ('resubmitted', 'Has been resubmitted'), ('voting_in_preparation', 'Voting in preparation (eligible Fellows being selected)'), ('put_to_EC_voting', 'Undergoing voting at the Editorial College'), ('EC_vote_completed', 'Editorial College voting rounded up'), ('accepted', 'Publication decision taken: accept'), ('rejected', 'Publication decision taken: reject'), ('published', 'Published'), ('withdrawn', 'Withdrawn by the Authors')], max_length=30),
        ),
    ]
