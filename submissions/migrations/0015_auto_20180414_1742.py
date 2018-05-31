# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-14 15:42
from __future__ import unicode_literals

from django.db import migrations

def merge_submission_statuses(apps, schema_editor):
    Submission = apps.get_model('submissions', 'Submission')

    # Rejected Submissions
    Submission.objects.filter(status='rejected_visible').update(status='rejected')

    # Resubmitted Submissions
    Submission.objects.filter(status__in=[
        'resubmitted_and_rejected',
        'resubmitted_and_rejected_visible']).update(status='resubmitted')

    # Rec. formulated Submissions
    Submission.objects.filter(status__in=[
        'voting_in_preparation',
        'put_to_EC_voting',
        'EC_vote_completed',
        'revision_requested']).update(status='recommendation_formulated')

    # Closed formulated Submissions
    Submission.objects.filter(status='review_closed').update(status='awaiting_ed_rec')

    # Incoming Submissions
    Submission.objects.filter(status__in=[
        'unassigned',
        'resubmitted_incoming']).update(status='unassigned_incoming')


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0014_auto_20180414_1729'),
    ]

    operations = [
        migrations.RunPython(merge_submission_statuses),
    ]
