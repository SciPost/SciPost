# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-14 15:29
from __future__ import unicode_literals

from django.db import migrations


def update_eic_rec_statuses(apps, schema_editor):
    Submission = apps.get_model('submissions', 'Submission')
    EICRecommendation = apps.get_model('submissions', 'EICRecommendation')

    # Update EICRecommendation statuses
    for sub in Submission.objects.filter(status='voting_in_preparation'):
        EICRecommendation.objects.filter(submission__id=sub.id).update(status='voting_in_prep')

    for sub in Submission.objects.filter(status='put_to_EC_voting'):
        EICRecommendation.objects.filter(submission__id=sub.id).update(status='put_to_voting')

    for sub in Submission.objects.filter(status='EC_vote_completed'):
        EICRecommendation.objects.filter(submission__id=sub.id).update(status='vote_completed')

    for sub in Submission.objects.filter(status__in=[
        'accepted',
        'published',
        'rejected',
        'rejected_visible',
        'resubmitted',
        'resubmitted_and_rejected',
        'resubmitted_and_rejected_visible',
        'revision_requested']):
        EICRecommendation.objects.filter(submission__id=sub.id).update(status='decision_fixed')


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0013_auto_20180414_1729'),
    ]

    operations = [
        migrations.RunPython(update_eic_rec_statuses),
    ]
