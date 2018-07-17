__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class NewsManager(models.Manager):
    def homepage(self):
        return self.filter(published=True, on_homepage=True)
