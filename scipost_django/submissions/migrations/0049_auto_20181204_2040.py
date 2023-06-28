# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-12-04 19:40
from __future__ import unicode_literals

import uuid

from django.db import migrations


def get_thread_ids(parent, submissions_list=[]):
    successor = parent.successor.first()
    if not successor:
        return submissions_list

    submissions_list.append(successor.id)
    return get_thread_ids(successor, submissions_list)


def populate_thread_hashes(apps, schema_editor):
    Submission = apps.get_model("submissions", "Submission")

    for original_submission in Submission.objects.filter(
        is_resubmission_of__isnull=True
    ):
        children_ids = get_thread_ids(original_submission, [original_submission.id])
        Submission.objects.filter(id__in=children_ids).update(
            thread_hash=original_submission.thread_hash
        )


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0048_submission_thread_hash"),
    ]

    operations = [
        migrations.RunPython(
            populate_thread_hashes, reverse_code=migrations.RunPython.noop
        ),
    ]
