__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from .constants import STATUS_PENDING


class CommentQuerySet(models.QuerySet):
    def vetted(self):
        return self.filter(status__gte=1)

    def awaiting_vetting(self):
        return self.filter(status=STATUS_PENDING)

    def regular_comments(self):
        return self.filter(is_author_reply=False)

    def author_replies(self):
        return self.filter(is_author_reply=True)
