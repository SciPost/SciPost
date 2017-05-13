import factory

from scipost.constants import DISCIPLINE_PHYSICS, SCIPOST_SUBJECT_AREAS
from scipost.factories import ContributorFactory
from journals.constants import SCIPOST_JOURNALS_DOMAINS
from common.helpers import random_arxiv_identifier_with_version_number

from .models import Commentary, COMMENTARY_TYPES


class CommentaryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Commentary
        abstract = True

    requested_by = factory.SubFactory(ContributorFactory)
    vetted_by = factory.SubFactory(ContributorFactory)
    type = COMMENTARY_TYPES[0][0]
    discipline = DISCIPLINE_PHYSICS
    domain = SCIPOST_JOURNALS_DOMAINS[0][0]
    subject_area = SCIPOST_SUBJECT_AREAS[0][1][0][0]
    pub_title = factory.Faker('bs')
    pub_DOI = '10.1103/PhysRevB.92.214427'
    arxiv_identifier = factory.Sequence(lambda n: random_arxiv_identifier_with_version_number())
    author_list = factory.Faker('name')
    pub_abstract = factory.Faker('text')
    pub_date = factory.Faker('date')

    @factory.post_generation
    def create_urls(self, create, extracted, **kwargs):
        self.parse_links_into_urls(commit=create)


class EmptyCommentaryFactory(CommentaryFactory):
    pub_DOI = None
    arxiv_identifier = None


class VettedCommentaryFactory(CommentaryFactory):
    vetted = True


class UnpublishedVettedCommentaryFactory(VettedCommentaryFactory):
    pub_DOI = ''


class UnvettedCommentaryFactory(CommentaryFactory):
    vetted = False

class UnvettedArxivPreprintCommentaryFactory(CommentaryFactory):
    vetted = False
    pub_DOI = None
