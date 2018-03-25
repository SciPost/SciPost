__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class CommentaryManager(models.Manager):
    def vetted(self, **kwargs):
        return self.filter(vetted=True, **kwargs)

    def awaiting_vetting(self, **kwargs):
        return self.filter(vetted=False, **kwargs)

    def open_for_commenting(self):
        return self.filter(open_for_commenting=True)
