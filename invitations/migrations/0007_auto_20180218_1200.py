# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-18 11:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0013_auto_20180216_0850'),
        ('submissions', '0008_auto_20180127_2208'),
        ('invitations', '0006_auto_20180217_1600'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registrationinvitation',
            name='cited_in_publication',
        ),
        migrations.RemoveField(
            model_name='registrationinvitation',
            name='cited_in_submission',
        ),
        migrations.AddField(
            model_name='registrationinvitation',
            name='cited_in_publications',
            field=models.ManyToManyField(blank=True, related_name='_registrationinvitation_cited_in_publications_+', to='journals.Publication'),
        ),
        migrations.AddField(
            model_name='registrationinvitation',
            name='cited_in_submissions',
            field=models.ManyToManyField(blank=True, related_name='_registrationinvitation_cited_in_submissions_+', to='submissions.Submission'),
        ),
    ]
