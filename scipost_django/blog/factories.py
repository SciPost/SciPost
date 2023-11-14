__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.utils.text import slugify
import factory

from common.faker import LazyAwareDate, LazyRandEnum
from scipost.factories import UserFactory

from .models import BlogPost, Category


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    title = factory.Faker("word")
    slug = factory.LazyAttribute(lambda self: slugify(self.title))
    description = factory.Faker("paragraph")


class BlogPostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlogPost

    status = LazyRandEnum(BlogPost.STATUS_CHOICES)
    title = factory.Faker("sentence")
    slug = factory.LazyAttribute(lambda self: slugify(self.title))
    blurb = factory.Faker("paragraph")
    blurb_image = factory.django.ImageField()
    blurb_image_caption = factory.Faker("paragraph")
    body = factory.Faker("paragraphs", nb=3)
    date_posted = LazyAwareDate("date_this_decade")
    posted_by = factory.SubFactory(UserFactory)
