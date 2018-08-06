__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.utils import timezone

from SciPost_v1.celery import app
from news.models import NewsItem


@app.task(bind=True)
def create_fake_news(self):
    now = timezone.now()
    NewsItem.objects.create(
        date=now,
        headline='Fakenews {}'.format(now.microsecond),
        blurb_short='Blurb short',
        blurb='Blurb full')
