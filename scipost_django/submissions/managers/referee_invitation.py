__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.utils import timezone


class RefereeInvitationQuerySet(models.QuerySet):
    """Queryset for RefereeInvitation model."""

    def auto_reminders_allowed(self):
        return self.filter(auto_reminders_allowed=True)

    def awaiting_response(self):
        """Filter sent invitations awaiting response by referee."""
        return self.filter(
            date_invited__isnull=False, accepted=None, cancelled=False, fulfilled=False
        )

    def accepted(self):
        """Filter invitations (non-cancelled) accepted by referee."""
        return self.filter(accepted=True, cancelled=False)

    def declined(self):
        """Filter invitations declined by referee."""
        return self.filter(accepted=False)

    def outstanding(self):
        return (
            self.filter(cancelled=False).exclude(accepted=False).exclude(fulfilled=True)
        )

    def in_process(self):
        """Filter invitations (non-cancelled) accepted by referee that are not fulfilled."""
        return self.accepted().filter(fulfilled=False, cancelled=False)

    def non_cancelled(self):
        """Return invitations awaiting reponse, accepted or fulfilled."""
        return self.filter(cancelled=False)

    def needs_attention(self):
        """Filter invitations that needs attention.

        The following is defined as `needs attention`:
        1. not responded to invite in more than 3 days.
        2. not fulfilled (but accepted) with deadline within 7 days.
        """
        compare_3_days = timezone.now() + datetime.timedelta(days=3)
        compare_7_days = timezone.now() + datetime.timedelta(days=7)
        return (
            self.filter(cancelled=False, fulfilled=False)
            .filter(
                models.Q(accepted=None, date_last_reminded__lt=compare_3_days)
                | models.Q(
                    accepted=True, submission__reporting_deadline__lt=compare_7_days
                )
            )
            .distinct()
        )

    def approaching_deadline(self, days=2):
        """Filter non-fulfilled invitations for which the deadline is within `days` days."""
        qs = self.in_process()
        pseudo_deadline = timezone.now() + datetime.timedelta(days)
        deadline = timezone.now()
        qs = qs.filter(
            submission__reporting_deadline__lte=pseudo_deadline,
            submission__reporting_deadline__gte=deadline,
        )
        return qs

    def overdue(self):
        """Filter non-fulfilled invitations that are overdue."""
        now = timezone.now()
        return self.in_process().filter(submission__reporting_deadline__lte=now)
