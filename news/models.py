from django.core.urlresolvers import reverse
from django.db import models

from .managers import NewsManager


class NewsItem(models.Model):
    date = models.DateField()
    headline = models.CharField(max_length=300)
    blurb = models.TextField()
    followup_link = models.URLField(blank=True)
    followup_link_text = models.CharField(max_length=300, blank=True)
    on_homepage = models.BooleanField(default=True)

    objects = NewsManager()

    class Meta:
        db_table = 'scipost_newsitem'
        ordering = ['-date']

    def __str__(self):
        return self.date.strftime('%Y-%m-%d') + ', ' + self.headline

    def get_absolute_url(self):
        return reverse('news:news') + '#news_' + str(self.id)
