import datetime
import hashlib
import random
import string

from django.db import models
from django.conf import settings
from django.utils import timezone

from . import constants
from .managers import RegistrationInvitationQuerySet

from scipost.constants import TITLE_CHOICES


class RegistrationInvitation(models.Model):
    """
    Invitation to particular persons for registration
    """
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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='invitations_created')

    # Related to objects
    invitation_type = models.CharField(max_length=2, choices=constants.INVITATION_TYPE,
                                       default=constants.INVITATION_CONTRIBUTOR)
    cited_in_submission = models.ManyToManyField('submissions.Submission',
                                                 blank=True, related_name='+')
    cited_in_publication = models.ManyToManyField('journals.Publication',
                                                  blank=True, related_name='+')

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

    def __str__(self):
        return '{} {} on {}'.format(self.first_name, self.last_name,
                                    self.created.strftime("%Y-%m-%d"))

    def save(self, *args, **kwargs):
        self.refresh_keys(commit=False)
        return super().save(*args, **kwargs)

    def refresh_keys(self, force_new_key=False, commit=True):
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
        if commit:
            self.save()

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
        self.times_sent = self.times_sent + 1
        self.save()
