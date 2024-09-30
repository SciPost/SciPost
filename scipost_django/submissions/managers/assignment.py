__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.db import models
from django.utils import timezone


class EditorialAssignmentQuerySet(models.QuerySet):
    def last_year(self):
        return self.filter(
            date_created__gt=timezone.now() - timezone.timedelta(days=365)
        )

    def last_two_years(self):
        return self.filter(
            date_created__gt=timezone.now() - timezone.timedelta(days=730)
        )

    def refereeing_deadline_within(self, days=7):
        now = timezone.now()
        return self.exclude(submission__reporting_deadline__isnull=True).filter(
            submission__reporting_deadline__lt=now + timezone.timedelta(days=days),
            submission__reporting_deadline__gt=now,
        )

    def next_invitation_to_be_sent(self, submission_id):
        """Return EditorialAssignment that needs to be sent next."""
        try:
            latest_date_invited = (
                self.invited()
                .filter(submission__id=submission_id, date_invited__isnull=False)
                .latest("date_invited")
                .date_invited
            )
            if latest_date_invited:
                return_next = (
                    latest_date_invited
                    < timezone.now() - settings.ED_ASSIGMENT_DT_DELTA
                )
            else:
                return_next = True
        except self.model.DoesNotExist:
            return_next = True

        if not return_next:
            return None

        return (
            self.filter(
                submission__id=submission_id, status=self.model.STATUS_PREASSIGNED
            )
            .order_by("invitation_order")
            .first()
        )

    def preassigned(self):
        return self.filter(status=self.model.STATUS_PREASSIGNED)

    def invited(self):
        return self.filter(status=self.model.STATUS_INVITED)

    def need_response(self):
        """Return EdAssignments that are non-deprecated or without response."""
        return self.filter(
            status__in=[self.model.STATUS_PREASSIGNED, self.model.STATUS_INVITED]
        )

    def ongoing(self):
        return self.filter(status=self.model.STATUS_ACCEPTED)

    def with_required_actions(self):
        ids = [o.id for o in self if o.submission.cycle.has_required_actions()]
        return self.filter(id__in=ids)

    def accepted(self):
        return self.filter(
            status__in=[self.model.STATUS_ACCEPTED, self.model.STATUS_COMPLETED]
        )

    def declined(self):
        return self.filter(status=self.model.STATUS_DECLINED)

    def declined_red(self):
        """Return EditorialAssignments declined with a 'red-label reason'."""
        return self.declined().filter(refusal_reason__in=["NIE", "DNP"])

    def deprecated(self):
        return self.filter(status=self.model.STATUS_DEPRECATED)

    def completed(self):
        return self.filter(status=self.model.STATUS_COMPLETED)


class ConditionalAssignmentOfferQuerySet(models.QuerySet):
    def offered(self):
        return self.filter(status=self.model.STATUS_OFFERED)
