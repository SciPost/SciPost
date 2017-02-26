from django.db import models

class CommentManager(models.Manager):
    def vetted(self):
        return self.filter(status__gte=1)
