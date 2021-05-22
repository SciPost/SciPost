__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from .models import NewsItem


class NewsItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NewsItem

    date = factory.Faker('date_this_year')
    headline = factory.Faker('sentence')
    blurb = factory.Faker('paragraph', nb_sentences=8)
    followup_link = factory.Faker('uri')
    followup_link_text = factory.Faker('sentence', nb_words=4)
