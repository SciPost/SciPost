__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import random
import factory

from commentaries.models import Commentary
from scipost.models import Contributor
from submissions.models import Submission, Report
from theses.models import ThesisLink

from .constants import STATUS_VETTED
from .models import Comment

from faker import Faker


class CommentFactory(factory.django.DjangoModelFactory):
    status = STATUS_VETTED
    vetted_by = factory.Iterator(Contributor.objects.all())

    author = factory.Iterator(Contributor.objects.all())
    comment_text = factory.Faker('paragraph')
    remarks_for_editors = factory.Faker('paragraph')
    file_attachment = Faker().file_name(extension='pdf')
    date_submitted = factory.Faker('date_this_decade')

    # Categories
    is_cor = factory.Faker('boolean', chance_of_getting_true=20)
    is_rem = factory.Faker('boolean', chance_of_getting_true=20)
    is_que = factory.Faker('boolean', chance_of_getting_true=20)
    is_ans = factory.Faker('boolean', chance_of_getting_true=20)
    is_obj = factory.Faker('boolean', chance_of_getting_true=20)
    is_rep = factory.Faker('boolean', chance_of_getting_true=20)
    is_val = factory.Faker('boolean', chance_of_getting_true=20)
    is_lit = factory.Faker('boolean', chance_of_getting_true=20)
    is_sug = factory.Faker('boolean', chance_of_getting_true=20)

    class Meta:
        model = Comment
        abstract = True


class CommentaryCommentFactory(CommentFactory):
    content_object = factory.Iterator(Commentary.objects.all())


class SubmissionCommentFactory(CommentFactory):
    content_object = factory.Iterator(Submission.objects.all())

    @factory.post_generation
    def replies(self, create, extracted, **kwargs):
        if create:
            for i in range(random.randint(0, 2)):
                ReplyCommentFactory(content_object=self)


class ReplyCommentFactory(CommentFactory):
    content_object = factory.SubFactory(SubmissionCommentFactory, replies=False)
    is_author_reply = factory.Faker('boolean')


class ThesislinkCommentFactory(CommentFactory):
    content_object = factory.Iterator(ThesisLink.objects.all())


class ReportCommentFactory(CommentFactory):
    content_object = factory.Iterator(Report.objects.all())
