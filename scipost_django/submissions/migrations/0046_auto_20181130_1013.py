# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-11-30 09:13
from __future__ import unicode_literals

from django.db import migrations


def populate_explicit_resubmission_links(apps, schema_editor):
    Submission = apps.get_model("submissions", "Submission")

    for resubmission in Submission.objects.filter(preprint__vn_nr__gt=1):
        resub_of = (
            Submission.objects.filter(
                preprint__identifier_wo_vn_nr=resubmission.preprint.identifier_wo_vn_nr,
                preprint__vn_nr__lt=resubmission.preprint.vn_nr,
            )
            .order_by("-preprint__vn_nr")
            .exclude(id=resubmission.id)
            .first()
        )
        Submission.objects.filter(id=resubmission.id).update(
            is_resubmission_of=resub_of
        )


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0045_submission_is_resubmission_of"),
    ]

    operations = [
        migrations.RunPython(
            populate_explicit_resubmission_links, reverse_code=migrations.RunPython.noop
        ),
    ]
