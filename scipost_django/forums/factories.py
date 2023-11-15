from django.utils.text import slugify
import factory

from common.faker import LazyAwareDate
from scipost.factories import UserFactory

from .models import Forum, Meeting, Motion, Post

from common.faker import fake


class ForumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Forum

    name = factory.Faker("sentence", nb_words=3)
    slug = factory.lazy_attribute(lambda self: slugify(self.name))
    description = factory.Faker("sentence")
    publicly_visible = True


class MeetingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Meeting

    forum = factory.SubFactory(ForumFactory)
    date_from = LazyAwareDate("date_this_year")
    date_until = factory.LazyAttribute(
        lambda self: fake.aware.date_between(start_date=self.date_from, end_date="+1y")
    )
    preamble = factory.Faker("paragraph")
    minutes = factory.Faker("paragraph")


class BasePostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post
        abstract = True

    posted_by = factory.SubFactory(UserFactory)
    posted_on = LazyAwareDate("date_this_year")
    needs_vetting = False
    vetted_by = factory.SubFactory(UserFactory)
    subject = factory.Faker("sentence")
    text = factory.Faker("paragraph")


class PostFactory(BasePostFactory):
    class Meta:
        model = Post

    # class Params:
    anchor = factory.SubFactory("forums.factories.ForumFactory")
    parent = factory.SelfAttribute("anchor")

    # parent_object_id = factory.SelfAttribute("anchored_to.id")
    # parent_content_type = factory.LazyAttribute(
    #     lambda self: django.contrib.contenttypes.models.ContentType.objects.get_for_model(
    #         self.anchored_to
    #     )
    # )
    # anchor_object_id = factory.SelfAttribute("anchored_to.id")
    # anchor_content_type = factory.LazyAttribute(
    #     lambda self: django.contrib.contenttypes.models.ContentType.objects.get_for_model(
    #         self.anchored_to
    #     )
    # )


class ReplyPostFactory(PostFactory):
    class Meta:
        model = Post

    # class Params:
    parent = factory.SubFactory("forums.factories.PostFactory")

    # parent_object_id = factory.SelfAttribute("reply_to.id")
    # parent_content_type = factory.LazyAttribute(
    #     lambda self: django.contrib.contenttypes.models.ContentType.objects.get_for_model(
    #         self.reply_to
    #     )
    # )


class MotionFactory(PostFactory):
    class Meta:
        model = Motion

    post = factory.SubFactory(PostFactory)
    voting_deadline = LazyAwareDate("date_this_year")
    accepted = False

    @factory.post_generation
    def eligible_for_voting(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.eligible_for_voting.add(user)
        else:
            self.eligible_for_voting.add(*UserFactory.create_batch(5))

    @factory.post_generation
    def in_agreement(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.in_agreement.add(user)

    @factory.post_generation
    def in_disagreement(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.in_disagreement.add(user)

    @factory.post_generation
    def in_abstain(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.in_abstain.add(user)

    @factory.post_generation
    def in_doubt(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.in_doubt.add(user)
