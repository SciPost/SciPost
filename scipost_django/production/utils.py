__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from guardian.shortcuts import assign_perm

from common.utils import BaseMailUtil


def proofs_id_to_slug(id):
    return int(id) + 8932


def proofs_slug_to_id(slug):
    return int(slug) - 8932


def get_or_create_production_stream(submission):
    """Get or create a ProductionStream for the given Submission."""
    from .models import ProductionStream

    prodstream, created = ProductionStream.objects.get_or_create(submission=submission)
    if created:
        ed_admins = Group.objects.get(name='Editorial Administrators')
        assign_perm('can_perform_supervisory_actions', ed_admins, prodstream)
        assign_perm('can_work_for_stream', ed_admins, prodstream)
    return prodstream


class ProductionUtils(BaseMailUtil):
    mail_sender = 'no-reply@%s' % Site.objects.get_current().domain
    mail_sender_title = 'SciPost Production'

    @classmethod
    def email_assigned_invitation_officer(cls):
        """
        Email invitation officer about his/her new assigned stream.
        """
        cls._send_mail(cls, 'email_assigned_invitation_officer',
                       [cls._context['stream'].invitations_officer.user.email],
                       'SciPost: you have a new task')

    @classmethod
    def email_assigned_production_officer(cls):
        """
        Email production officer about his/her new assigned stream.
        """
        cls._send_mail(cls, 'email_assigned_production_officer',
                       [cls._context['stream'].officer.user.email],
                       'SciPost: you have a new task')

    @classmethod
    def email_assigned_supervisor(cls):
        """
        Email production officer about his/her new assigned stream.
        """
        cls._send_mail(cls, 'email_assigned_supervisor',
                       [cls._context['stream'].supervisor.user.email],
                       'SciPost: you have a new supervisory task')
