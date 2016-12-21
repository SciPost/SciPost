import factory

from .models import Commentary, COMMENTARY_TYPES

from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.factories import ContributorFactory
from journals.models import SCIPOST_JOURNALS_DOMAINS


class CommentaryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Commentary
        abstract = True

    requested_by = factory.SubFactory(ContributorFactory)
    vetted_by = factory.SubFactory(ContributorFactory)
    type = COMMENTARY_TYPES[0][0]
    discipline = SCIPOST_DISCIPLINES[0][0]
    domain = SCIPOST_JOURNALS_DOMAINS[0][0]
    subject_area = SCIPOST_SUBJECT_AREAS[0][1][0][0]
    pub_title = factory.Sequence(lambda n: "Commentary %d" % n)
    pub_DOI = '10.1103/PhysRevB.92.214427'
    arxiv_identifier = '1610.06911v1'
    author_list = factory.Faker('name')
    pub_abstract = factory.Faker('text')


class EmptyCommentaryFactory(CommentaryFactory):
    pub_DOI = None
    arxiv_identifier = None


class VettedCommentaryFactory(CommentaryFactory):
    vetted = True
