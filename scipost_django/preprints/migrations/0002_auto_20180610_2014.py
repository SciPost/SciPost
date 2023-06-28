# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-10 18:14
from __future__ import unicode_literals
from datetime import datetime

from django.db import migrations


def remove_all_preprints(apps, schema_editor):
    Preprint = apps.get_model("preprints", "Preprint")
    Preprint.objects.all().delete()
    return


def create_preprint_instances(apps, schema_editor):
    """Add a Preprint instance for each existing Submission."""
    Preprint = apps.get_model("preprints", "Preprint")
    Submission = apps.get_model("submissions", "Submission")

    for submission in Submission.objects.all():
        dt = datetime(
            year=submission.submission_date.year,
            month=submission.submission_date.month,
            day=submission.submission_date.day,
        )
        Preprint.objects.get_or_create(
            submission=submission,
            identifier_wo_vn_nr=submission.arxiv_identifier_wo_vn_nr,
            identifier_w_vn_nr=submission.arxiv_identifier_w_vn_nr,
            vn_nr=submission.arxiv_vn_nr,
            url=submission.arxiv_link,
            modified=submission.latest_activity,
            created=dt,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("preprints", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_preprint_instances, remove_all_preprints),
    ]
