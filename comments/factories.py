import factory
import pytz

from django.utils import timezone

from commentaries.factories import VettedCommentaryFactory
from scipost.factories import ContributorFactory
from submissions.factories import EICassignedSubmissionFactory
from theses.factories import VettedThesisLinkFactory

from .constants import STATUS_VETTED
from .models import Comment

from faker import Faker

timezone.now()


class CommentFactory(factory.django.DjangoModelFactory):
    author = factory.SubFactory(ContributorFactory)
    comment_text = factory.lazy_attribute(lambda x: Faker().paragraph())
    remarks_for_editors = factory.lazy_attribute(lambda x: Faker().paragraph())
    file_attachment = Faker().file_name(extension='pdf')
    status = STATUS_VETTED  # All comments will have status vetted!
    vetted_by = factory.SubFactory(ContributorFactory)
    date_submitted = Faker().date_time_between(start_date="-3y", end_date="now", tzinfo=pytz.UTC)

    class Meta:
        model = Comment
        abstract = True


class CommentaryCommentFactory(CommentFactory):
    commentary = factory.SubFactory(VettedCommentaryFactory)


class SubmissionCommentFactory(CommentFactory):
    submission = factory.SubFactory(EICassignedSubmissionFactory)


class ThesislinkCommentFactory(CommentFactory):
    thesislink = factory.SubFactory(VettedThesisLinkFactory)


class ReplyCommentFactory(CommentFactory):
    in_reply_to_comment = factory.SubFactory(SubmissionCommentFactory)
