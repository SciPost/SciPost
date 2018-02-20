# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-20 10:39
from __future__ import unicode_literals
import datetime
import hashlib
import random
import string

from django.utils import timezone
from django.db import migrations

# Hack
from django.contrib.auth import get_user_model


def transfer_old_invitations_to_new_tables(apps, schema_editor):
    OldDraftInvitation = apps.get_model('scipost', 'DraftInvitation')
    OldRegistrationInvitation = apps.get_model('scipost', 'RegistrationInvitation')
    OldCitationNotification = apps.get_model('scipost', 'CitationNotification')
    NewRegistrationInvitation = apps.get_model('invitations', 'RegistrationInvitation')
    NewCitationNotification = apps.get_model('invitations', 'CitationNotification')

    random_user = get_user_model().objects.filter(is_superuser=True).first()
    if not random_user:
        random_user = get_user_model().objects.first()

    # Registration Invitations first
    for invitation in OldRegistrationInvitation.objects.all():
        new_inv = NewRegistrationInvitation(
            title=invitation.title,
            first_name=invitation.first_name,
            last_name=invitation.last_name,
            email=invitation.email,
            invitation_type=invitation.invitation_type,
            created_by_id=invitation.invited_by.user.id if invitation.invited_by else random_user.id,
            invited_by_id=invitation.invited_by.user.id if invitation.invited_by else None,
            message_style=invitation.message_style,
            personal_message=invitation.personal_message,
            times_sent=invitation.nr_reminders + 1,
            date_sent_first=invitation.date_sent,
            date_sent_last=invitation.date_last_reminded,
            created=invitation.date_sent,
            modified=invitation.date_sent,
            key_expires=invitation.key_expires,
            invitation_key=invitation.invitation_key,
        )
        if new_inv.invitation_type in ['ci', 'cp']:
            new_inv.invitation_type = 'C'

        if not invitation.responded:
            new_inv.status = 'sent'
        elif invitation.declined:
            new_inv.status = 'declined'
        elif invitation.responded and not invitation.declined:
            new_inv.status = 'register'
        else:
            new_inv.status = 'draft'
        new_inv.save()

        if invitation.cited_in_submission:
            NewCitationNotification.objects.create(
                invitation_id=new_inv.id,
                created_by_id=invitation.invited_by.user.id if invitation.invited_by else random_user.id,
                created=new_inv.created,
                modified=new_inv.modified,
                submission_id=invitation.cited_in_submission.id,
                date_sent=invitation.date_last_reminded,
                processed=(new_inv.status in ['declined', 'register', 'sent']),
            )
        if invitation.cited_in_publication:
            NewCitationNotification.objects.create(
                invitation_id=new_inv.id,
                created_by_id=invitation.invited_by.user.id if invitation.invited_by else random_user.id,
                created=new_inv.created,
                modified=new_inv.modified,
                publication_id=invitation.cited_in_publication.id,
                date_sent=invitation.date_last_reminded,
                processed=(new_inv.status in ['declined', 'register', 'sent']),
            )

    # Draft Invitations
    for invitation in OldDraftInvitation.objects.filter(processed=False):
        new_inv = NewRegistrationInvitation(
            title=invitation.title,
            first_name=invitation.first_name,
            last_name=invitation.last_name,
            email=invitation.email,
            invitation_type=invitation.invitation_type,
            created_by_id=invitation.drafted_by.user.id if invitation.drafted_by else random_user.id,
            invited_by_id=None,
            times_sent=0,
            date_sent_first=None,
            date_sent_last=None,
            created=invitation.date_drafted,
            modified=invitation.date_drafted,
            status='draft',
        )
        if new_inv.invitation_type in ['ci', 'cp']:
            new_inv.invitation_type = 'C'

        # Generate keys, custom methods are not loaded here
        salt = ''
        for i in range(5):
            salt += random.choice(string.ascii_letters)
        salt = salt.encode('utf8')
        invitationsalt = new_inv.last_name.encode('utf8')
        new_inv.invitation_key = hashlib.sha1(salt + invitationsalt).hexdigest()
        new_inv.key_expires = timezone.now() + datetime.timedelta(days=365)
        new_inv.save()

        if invitation.cited_in_submission:
            NewCitationNotification.objects.create(
                invitation_id=new_inv.id,
                created_by_id=invitation.drafted_by.user.id if invitation.drafted_by else random_user.id,
                created=new_inv.created,
                modified=new_inv.modified,
                submission_id=invitation.cited_in_submission.id,
                date_sent=None,
                processed=False,
            )
        if invitation.cited_in_publication:
            NewCitationNotification.objects.create(
                invitation_id=new_inv.id,
                created_by_id=invitation.drafted_by.user.id if invitation.drafted_by else random_user.id,
                created=new_inv.created,
                modified=new_inv.modified,
                publication_id=invitation.cited_in_publication.id,
                date_sent=None,
                processed=False,
            )

    # Old CitationNotifications
    for notification in OldCitationNotification.objects.all():
        NewCitationNotification.objects.create(
            contributor_id=notification.contributor.id if notification.contributor else None,
            created_by_id=random_user.id,
            submission_id=notification.cited_in_submission.id if notification.cited_in_submission else None,
            publication_id=notification.cited_in_publication.id if notification.cited_in_publication else None,
            processed=notification.processed,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0010_auto_20180218_1613'),
    ]

    operations = [
        migrations.RunPython(transfer_old_invitations_to_new_tables),
    ]
