# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-09-14 04:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0022_auto_20160822_1934'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='status',
            field=models.CharField(choices=[('unassigned', 'Unassigned, undergoing pre-screening'), ('assignment_failed', 'Failed to assign Editor-in-charge; manuscript rejected'), ('EICassigned', 'Editor-in-charge assigned, manuscript under review'), ('review_closed', 'Review period closed, editorial recommendation pending'), ('revision_requested', 'Editor-in-charge has requested revision'), ('resubmitted', 'Has been resubmitted'), ('voting_in_preparation', 'Voting in preparation (eligible Fellows being selected)'), ('put_to_EC_voting', 'Undergoing voting at the Editorial College'), ('EC_vote_completed', 'Editorial College voting rounded up'), ('accepted', 'Publication decision taken: accept'), ('rejected', 'Publication decision taken: reject'), ('rejected_visible', 'Publication decision taken: reject (still publicly visible)'), ('published', 'Published'), ('withdrawn', 'Withdrawn by the Authors')], max_length=30),
        ),
    ]
