__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from .. import constants


class ReportQuerySet(models.QuerySet):
    """QuerySet for the Report model."""

    def accepted(self):
        """Return the subset of vetted Reports."""
        return self.filter(status=constants.STATUS_VETTED)

    def awaiting_vetting(self):
        """Return the subset of unvetted Reports."""
        return self.filter(status=constants.STATUS_UNVETTED)

    def rejected(self):
        """Return the subset of rejected Reports."""
        return self.filter(status__in=[
            constants.STATUS_UNCLEAR, constants.STATUS_INCORRECT, constants.STATUS_NOT_USEFUL,
            constants.STATUS_NOT_ACADEMIC])

    def in_draft(self):
        """Return the subset of Reports in draft."""
        return self.filter(status=constants.STATUS_DRAFT)

    def non_draft(self):
        """Return the subset of unvetted, vetted and rejected Reports."""
        return self.exclude(status=constants.STATUS_DRAFT)

    def contributed(self):
        """Return the subset of contributed Reports."""
        return self.filter(invited=False)

    def invited(self):
        """Return the subset of invited Reports."""
        return self.filter(invited=True)
