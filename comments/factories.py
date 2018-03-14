import factory
import pytz

from django.utils import timezone

from commentaries.factories import CommentaryFactory
from scipost.models import Contributor
from submissions.factories import EICassignedSubmissionFactory
from theses.factories import VettedThesisLinkFactory

from .constants import STATUS_VETTED
from .models import Comment

from faker import Faker

timezone.now()


class CommentFactory(factory.django.DjangoModelFactory):
    author = factory.Iterator(Contributor.objects.all())
    comment_text = factory.lazy_attribute(lambda x: Faker().paragraph())
    remarks_for_editors = factory.lazy_attribute(lambda x: Faker().paragraph())
    file_attachment = Faker().file_name(extension='pdf')
    status = STATUS_VETTED  # All comments will have status vetted!
    vetted_by = factory.Iterator(Contributor.objects.all())
    date_submitted = Faker().date_time_between(start_date="-3y", end_date="now", tzinfo=pytz.UTC)

    class Meta:
        model = Comment
        abstract = True


class CommentaryCommentFactory(CommentFactory):
    content_object = factory.SubFactory(CommentaryFactory)


class SubmissionCommentFactory(CommentFactory):
    content_object = factory.SubFactory(EICassignedSubmissionFactory)


class ThesislinkCommentFactory(CommentFactory):
    content_object = factory.SubFactory(VettedThesisLinkFactory)


class ReplyCommentFactory(CommentFactory):
    content_object = factory.SubFactory(SubmissionCommentFactory)
