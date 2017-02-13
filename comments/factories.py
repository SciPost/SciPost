import factory

from django.utils import timezone

from .models import Comment


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    comment_text = factory.Faker('text')
    date_submitted = timezone.now()
