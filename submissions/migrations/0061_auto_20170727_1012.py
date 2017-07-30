# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-07-27 08:12
from __future__ import unicode_literals

from django.db import migrations

from guardian.shortcuts import assign_perm

from ..models import Report


def do_nothing(apps, schema_editor):
    return


def update_eic_permissions(apps, schema_editor):
    """
    Grant EIC of submission related to unvetted Reports
    permission to vet his submission's Report.
    """
    # Report = apps.get_model('submissions', 'Report')  -- This doesn't work due to shitty imports
    count = 0
    for rep in Report.objects.filter(status='unvetted'):
        eic_user = rep.submission.editor_in_charge
        assign_perm('submissions.can_vet_submitted_reports', eic_user.user, rep)
        count += 1
    print('\nGranted permission to %i Editor(s)-in-charge to vet related Reports.' % count)


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0060_merge_20170726_0945'),
    ]

    operations = [
        migrations.RunPython(update_eic_permissions, do_nothing),
    ]
