__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.sites.models import Site

from common.utils import BaseMailUtil


class Utils(BaseMailUtil):
    mail_sender = "invitations@%s" % Site.objects.get_current().domain
    mail_sender_title = "SciPost Invitation"

    @classmethod
    def invite_contributor_email(cls):
        """
        Send email to unregistered people inviting them to become a SciPost Contributor.
        Requires context to contain 'registration_invitation' (RegistrationInvitation instance).
        """
        raise NotImplementedError("invite_contributor_email")

    @classmethod
    def invite_contributor_reminder_email(cls):
        """
        Send reminder(!) email to unregistered people inviting them to become a SciPost
        Contributor.
        Requires context to contain 'registration_invitation'(RegistrationInvitation instance).
        """
        raise NotImplementedError("invite_contributor_reminder_email")

    @classmethod
    def citation_notifications_email(cls):
        """
        Send email to a SciPost Contributor about a Citation Notification that's been created
        for him/her. Requires context to contain 'notifications' (list of CitationNotifications).
        """
        raise NotImplementedError("citation_notifications_email")
