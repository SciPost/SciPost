from django.db import models


class NewsManager(models.Manager):
    def homepage(self):
        return self.filter(on_homepage=True)
