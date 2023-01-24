__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class ReadinessQuerySet(models.QuerySet):

    def perhaps_later(self):
        return self.filter(status=self.model.STATUS_PERHAPS_LATER)

    def could_if_transferred(self):
        return self.filter(status=self.model.STATUS_COULD_IF_TRANSFERRED)

    def too_busy(self):
        return self.filter(status=self.model.STATUS_TOO_BUSY)

    def not_interested(self):
        return self.filter(status=self.model.STATUS_NOT_INTERESTED)

    def vote_for_desk_rejection(self):
        return self.filter(status=self.model.STATUS_VOTE_FOR_DESK_REJECTION)
