from django.db import models


class NewsItem(models.Model):
    date = models.DateField()
    headline = models.CharField(max_length=300)
    blurb = models.TextField()
    followup_link = models.URLField(blank=True, null=True)
    followup_link_text = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        db_table = 'scipost_newsitem'

    def __str__(self):
        return self.date.strftime('%Y-%m-%d') + ', ' + self.headline
