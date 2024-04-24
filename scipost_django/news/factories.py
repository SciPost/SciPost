__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from .models import NewsItem, NewsCollection


class NewsCollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NewsCollection

    date = factory.Faker("date_this_year")
    intro = factory.Faker("paragraph", nb_sentences=2)
    closing = factory.Faker("paragraph", nb_sentences=2)
    published = True

    # Create NewsItems for this NewsCollection linking them through NewsCollectionNewsItemsTable
    @factory.post_generation
    def news_items(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for news_item in extracted:
                self.news_items.add(news_item)

        self.news_items = NewsItemFactory.create_batch(3)


class NewsItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NewsItem

    date = factory.Faker("date_this_year")
    headline = factory.Faker("sentence")
    blurb = factory.Faker("paragraph", nb_sentences=8)
    blurb_short = factory.Faker("paragraph", nb_sentences=3)
    followup_link = factory.Faker("uri")
    followup_link_text = factory.Faker("sentence", nb_words=4)
    published = True
