__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class BlogPostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=self.model.PUBLISHED)
