import factory

from .models import NewsItem


class NewsItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NewsItem

    date = factory.Faker('date_time')
    headline = factory.Faker('sentence', nb_words=6)
    blurb = factory.Faker('text', max_nb_chars=200)
    followup_link = factory.Faker('url')
    followup_link_text = factory.Faker('sentence', nb_words=4)
