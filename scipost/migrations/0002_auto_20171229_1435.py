# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import scipost.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('submissions', '0001_initial'),
        ('commentaries', '0002_auto_20171229_1435'),
        # Deprec virtualmeetings 2019-04-05
        # ('virtualmeetings', '0001_initial'),
        ('journals', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('theses', '0001_initial'),
        ('scipost', '0001_initial'),
    ]

    operations = [
        # Deprec virtualmeetings 2019-04-05
        # migrations.AddField(
        #     model_name='remark',
        #     name='feedback',
        #     field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='remarks', to='virtualmeetings.Feedback'),
        # ),
        # migrations.AddField(
        #     model_name='remark',
        #     name='motion',
        #     field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='remarks', to='virtualmeetings.Motion'),
        # ),
        # migrations.AddField(
        #     model_name='remark',
        #     name='nomination',
        #     field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='remarks', to='virtualmeetings.Nomination'),
        # ),
        migrations.AddField(
            model_name='remark',
            name='recommendation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='remarks', to='submissions.EICRecommendation'),
        ),
        migrations.AddField(
            model_name='remark',
            name='submission',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='remarks', to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='registrationinvitation',
            name='cited_in_publication',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='journals.Publication'),
        ),
        migrations.AddField(
            model_name='registrationinvitation',
            name='cited_in_submission',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='registration_invitations', to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='registrationinvitation',
            name='invited_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='editorialcollegefellowship',
            name='college',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fellowships', to='scipost.EditorialCollege'),
        ),
        migrations.AddField(
            model_name='editorialcollegefellowship',
            name='contributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='draftinvitation',
            name='cited_in_publication',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='journals.Publication'),
        ),
        migrations.AddField(
            model_name='draftinvitation',
            name='cited_in_submission',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='draftinvitation',
            name='drafted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='contributor',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='contributor',
            name='vetted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET(scipost.models.get_sentinel_user), related_name='contrib_vetted_by', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='citationnotification',
            name='cited_in_publication',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='journals.Publication'),
        ),
        migrations.AddField(
            model_name='citationnotification',
            name='cited_in_submission',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='citationnotification',
            name='contributor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='authorshipclaim',
            name='claimant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='claimant', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='authorshipclaim',
            name='commentary',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='commentaries.Commentary'),
        ),
        migrations.AddField(
            model_name='authorshipclaim',
            name='publication',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='journals.Publication'),
        ),
        migrations.AddField(
            model_name='authorshipclaim',
            name='submission',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='submissions.Submission'),
        ),
        migrations.AddField(
            model_name='authorshipclaim',
            name='thesislink',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='theses.ThesisLink'),
        ),
        migrations.AddField(
            model_name='authorshipclaim',
            name='vetted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scipost.Contributor'),
        ),
        migrations.AlterUniqueTogether(
            name='editorialcollegefellowship',
            unique_together=set([('contributor', 'college', 'start_date', 'until_date')]),
        ),
    ]
