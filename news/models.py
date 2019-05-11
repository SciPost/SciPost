__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import reverse
from django.db import models

from .managers import NewsManager


class NewsLetter(models.Model):
    """
    Container of NewsItems.
    Which NewsItems (and their order) are handled via the auxiliary
    model NewsLetterNewsItemsTable.
    """
    date = models.DateField()
    intro = models.TextField()
    closing = models.TextField()
    published = models.BooleanField(default=False)

    def __str__(self):
        return 'SciPost Newsletter %s' % self.date.strftime('%Y-%m-%d')

    def get_absolute_url(self):
        return reverse('news:newsletter_detail',
                       kwargs={'year': self.date.strftime('%Y'),
                               'month': self.date.strftime('%m'),
                               'day': self.date.strftime('%d')})


class NewsItem(models.Model):
    date = models.DateField()
    headline = models.CharField(max_length=300)
    blurb_short = models.TextField(default='',
                                   help_text='Short version for use in Newsletter/emails etc')
    blurb = models.TextField()
    image = models.ImageField(upload_to='news/newsitems/%Y/', blank=True)
    css_class = models.CharField(max_length=256, blank=True,
                                 verbose_name='Additional image CSS class')
    followup_link = models.URLField(blank=True)
    followup_link_text = models.CharField(max_length=300, blank=True)
    published = models.BooleanField(default=False)
    on_homepage = models.BooleanField(default=True)

    objects = NewsManager()

    class Meta:
        db_table = 'scipost_newsitem'
        ordering = ['-date']

    def __str__(self):
        return self.date.strftime('%Y-%m-%d') + ', ' + self.headline

    def get_absolute_url(self):
        return reverse('news:news') + '#news_' + str(self.id)


class NewsLetterNewsItemsTable(models.Model):
    """
    Carries the specification of which NewsItem sits in which NewsLetter,
    and in which order.
    """
    newsletter = models.ForeignKey('news.NewsLetter', on_delete=models.CASCADE)
    newsitem = models.ForeignKey('news.NewsItem', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()
