__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import hashlib
import random
import string

from django.db import models, IntegrityError
from django.conf import settings
from django.utils import timezone

from . import constants
from .managers import RegistrationInvitationQuerySet, CitationNotificationQuerySet

from scipost.constants import TITLE_CHOICES


class RegistrationInvitation(models.Model):
    """
    Invitation to particular persons for registration
    """
    profile = models.ForeignKey('profiles.Profile', on_delete=models.SET_NULL,
                                blank=True, null=True)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    status = models.CharField(max_length=8, choices=constants.REGISTATION_INVITATION_STATUSES,
                              default=constants.STATUS_DRAFT)

    # Text content
    message_style = models.CharField(max_length=1, choices=constants.INVITATION_STYLE,
                                     default=constants.INVITATION_FORMAL)
    personal_message = models.TextField(blank=True)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   blank=True, null=True, related_name='invitations_sent')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   related_name='invitations_created')

    # Related to objects
    invitation_type = models.CharField(max_length=2, choices=constants.INVITATION_TYPE,
                                       default=constants.INVITATION_CONTRIBUTOR)

    # Response keys
    invitation_key = models.CharField(max_length=40, unique=True)
    key_expires = models.DateTimeField(default=timezone.now)

    # Timestamps
    date_sent_first = models.DateTimeField(null=True, blank=True)
    date_sent_last = models.DateTimeField(null=True, blank=True)
    times_sent = models.PositiveSmallIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = RegistrationInvitationQuerySet.as_manager()

    class Meta:
        ordering = ['last_name']

    def __init__(self, *args, **kwargs):
        response = super().__init__(*args, **kwargs)
        self.refresh_keys()
        return response

    def __str__(self):
        return '{} {} on {}'.format(self.first_name, self.last_name,
                                    self.created.strftime("%Y-%m-%d"))

    def refresh_keys(self, force_new_key=False):
        # Generate email activation key and link
        if not self.invitation_key or force_new_key:
            # TODO: Replace this all by the `secrets` package available from python 3.6(!)
            salt = ''
            for i in range(5):
                salt += random.choice(string.ascii_letters)
            salt = salt.encode('utf8')
            invitationsalt = self.last_name.encode('utf8')
            self.invitation_key = hashlib.sha1(salt + invitationsalt).hexdigest()
            self.key_expires = timezone.now() + datetime.timedelta(days=365)

    def mail_sent(self, user=None):
        """
        Update instance fields as if a new invitation mail has been sent out.
        """
        if self.status == constants.STATUS_DRAFT:
            self.status = constants.STATUS_SENT
        if not self.date_sent_first:
            self.date_sent_first = timezone.now()
        self.date_sent_last = timezone.now()
        self.invited_by = user or self.created_by
        self.times_sent += 1
        self.citation_notifications.update(processed=True)
        self.save()

    @property
    def has_responded(self):
        return self.status in [constants.STATUS_DECLINED, constants.STATUS_REGISTERED]


class CitationNotification(models.Model):
    invitation = models.ForeignKey('invitations.RegistrationInvitation',
                                   on_delete=models.CASCADE,
                                   null=True, blank=True)
    contributor = models.ForeignKey('scipost.Contributor',
                                    on_delete=models.CASCADE,
                                    null=True, blank=True,
                                    related_name='+')

    # Content
    submission = models.ForeignKey('submissions.Submission', null=True, blank=True,
                                   on_delete=models.CASCADE, related_name='+')
    publication = models.ForeignKey('journals.Publication', null=True, blank=True,
                                    on_delete=models.CASCADE, related_name='+')
    processed = models.BooleanField(default=False)

    # Meta info
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   related_name='notifications_created')
    date_sent = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = CitationNotificationQuerySet.as_manager()

    class Meta:
        default_related_name = 'citation_notifications'
        unique_together = (
            ('invitation', 'submission'),
            ('invitation', 'publication'),
            ('contributor', 'submission'),
            ('contributor', 'publication'),
        )

    def __str__(self):
        _str = 'Citation for '
        if self.invitation:
            _str += ' Invitation ({} {})'.format(
                self.invitation.first_name,
                self.invitation.last_name,
            )
        elif self.contributor:
            _str += ' Contributor ({})'.format(self.contributor)

        _str += ' on '
        if self.submission:
            _str += 'Submission ({})'.format(self.submission.preprint.identifier_w_vn_nr)
        elif self.publication:
            _str += 'Publication ({})'.format(self.publication.doi_label)
        return _str

    def save(self, *args, **kwargs):
        if not self.submission and not self.publication:
            raise IntegrityError(('CitationNotification needs to be related to either a '
                                  'Submission or Publication object.'))
        return super().save(*args, **kwargs)

    def mail_sent(self):
        """
        Update instance fields as if a new citation notification mail has been sent out.
        """
        self.processed = True
        if not self.date_sent:
            # Don't overwrite by accident...
            self.date_sent = timezone.now()
        self.save()

    def related_notifications(self):
        return CitationNotification.objects.unprocessed().filter(
            models.Q(contributor=self.contributor) | models.Q(invitation=self.invitation))

    def get_first_related_contributor(self):
        return self.related_notifications().filter(contributor__isnull=False).first()

    @property
    def email(self):
        if self.invitation:
            return self.invitation.email
        elif self.contributor:
            return self.contributor.user.email

    @property
    def last_name(self):
        if self.invitation:
            return self.invitation.last_name
        elif self.contributor:
            return self.contributor.user.last_name

    @property
    def get_title(self):
        if self.invitation:
            return self.invitation.get_title_display()
        elif self.contributor and self.contributor.profile:
            return self.contributor.profile.get_title_display()
