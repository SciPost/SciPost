# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-04-15 08:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0035_auto_20170407_0954'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='refereeing_cycle',
            field=models.CharField(choices=[('default', 'Default cycle'), ('short', 'Short cycle'), ('direct_rec', 'Direct editorial recommendation')], default='default', max_length=30),
        ),
        migrations.AlterField(
            model_name='submission',
            name='status',
            field=models.CharField(choices=[('unassigned', 'Unassigned, undergoing pre-screening'), ('resubmitted_incomin', 'Resubmission incoming, undergoing pre-screening'), ('assignment_failed', 'Failed to assign Editor-in-charge; manuscript rejected'), ('EICassigned', 'Editor-in-charge assigned, manuscript under review'), ('review_closed', 'Review period closed, editorial recommendation pending'), ('revision_requested', 'Editor-in-charge has requested revision'), ('resubmitted', 'Has been resubmitted'), ('resubmitted_and_rejected', 'Has been resubmitted and subsequently rejected'), ('resubmitted_and_rejected_visible', 'Has been resubmitted and subsequently rejected (still publicly visible)'), ('voting_in_preparation', 'Voting in preparation (eligible Fellows being selected)'), ('put_to_EC_voting', 'Undergoing voting at the Editorial College'), ('EC_vote_completed', 'Editorial College voting rounded up'), ('accepted', 'Publication decision taken: accept'), ('rejected', 'Publication decision taken: reject'), ('rejected_visible', 'Publication decision taken: reject (still publicly visible)'), ('published', 'Published'), ('withdrawn', 'Withdrawn by the Authors')], default='unassigned', max_length=30),
        ),
    ]
