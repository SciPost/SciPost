__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from .constants import (
    TICKET_STATUS_UNASSIGNED, TICKET_STATUS_ASSIGNED,
    TICKET_STATUS_RESOLVED, TICKET_STATUS_CLOSED)


class QueueQuerySet(models.QuerySet):

    def anchors(self):
        """Return only Queues which have no parent Queue."""
        return self.filter(parent_queue__isnull=True)


class TicketQuerySet(models.QuerySet):

    def unassigned(self):
        return self.filter(status=TICKET_STATUS_UNASSIGNED)

    def assigned(self):
        return self.filter(status=TICKET_STATUS_ASSIGNED)

    def resolved(self):
        return self.filter(status=TICKET_STATUS_RESOLVED)

    def closed(self):
        return self.filter(status=TICKET_STATUS_CLOSED)