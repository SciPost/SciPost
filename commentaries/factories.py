__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from scipost.constants import SCIPOST_APPROACHES
from scipost.models import Contributor
from common.helpers import random_arxiv_identifier_with_version_number, random_external_doi
from ontology.models import AcademicField, Specialty

from .constants import COMMENTARY_TYPES
from .models import Commentary


class BaseCommentaryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Commentary
        django_get_or_create = ('pub_DOI', 'arxiv_identifier')
        abstract = True

    requested_by = factory.SubFactory('scipost.factories.ContributorFactory')
    vetted = True
    vetted_by = factory.SubFactory('scipost.factories.ContributorFactory')
    type = factory.Iterator(COMMENTARY_TYPES, getter=lambda c: c[0])
    acad_field = factory.SubFactory('ontology.factories.AcademicFieldFactory')
    approaches = factory.Iterator(SCIPOST_APPROACHES, getter=lambda c: [c[0],])
    open_for_commenting = True

    title = factory.Faker('sentence')
    arxiv_identifier = factory.Sequence(lambda n: random_arxiv_identifier_with_version_number('1'))
    #arxiv_link
    pub_DOI = factory.Sequence(lambda n: random_external_doi())
    #pub_DOI_link
    #metadata
    arxiv_or_DOI_string = factory.lazy_attribute(lambda o: (
        o.arxiv_identifier if o.arxiv_identifier else o.pub_DOI))
    #scipost_publication
    author_list = factory.Faker('name')
    #authors
    #authors_claims
    #authors_false_claims
    #journal
    #volume
    #pages
    pub_date = factory.Faker('date_this_decade')
    pub_abstract = factory.Faker('paragraph')
    #comments

    # url = factory.lazy_attribute(lambda o: 'https://arxiv.org/abs/%s' % o.arxiv_identifier)

    @classmethod
    def create(cls, **kwargs):
        if AcademicField.objects.count() < 5:
            from ontology.factories import AcademicFieldactory
            AcademicFieldFactory.create_batch(5)
        if Specialty.objects.count() < 5:
            from ontology.factories import SpecialtyFactory
            SpecialtyFactory.create_batch(5)
        return super().create(**kwargs)

    @factory.post_generation
    def add_specialties(self, create, extracted, **kwargs):
        if create:
            self.specialties.set(Specialty.objects.order_by('?')[:3])

    @factory.post_generation
    def create_urls(self, create, extracted, **kwargs):
        self.parse_links_into_urls(commit=create)

    @factory.post_generation
    def add_authors(self, create, extracted, **kwargs):
        contributors = Contributor.objects.order_by('?').exclude(pk=self.requested_by.pk)[:4]
        self.author_list = ', '.join(
            ['%s %s' % (contrib.user.first_name, contrib.user.last_name)
                for contrib in contributors])

        if create:
            self.authors.add(*contributors)

    @factory.post_generation
    def set_journal_data(self, create, extracted, **kwargs):
        if not self.pub_DOI:
            return

        data = self.pub_DOI.split('/')[1].split('.')
        self.journal = data[0]
        self.volume = data[1]
        self.pages = data[2]


class CommentaryFactory(BaseCommentaryFactory):
    pass


class UnvettedCommentaryFactory(BaseCommentaryFactory):
    vetted = False
    vetted_by = None


class UnpublishedCommentaryFactory(BaseCommentaryFactory):
    pub_DOI = ''
    pub_date = None


class UnvettedUnpublishedCommentaryFactory(UnpublishedCommentaryFactory):
    vetted = False
    vetted_by = None


class PublishedCommentaryFactory(BaseCommentaryFactory):
    arxiv_identifier = ''
    url = ''
    arxiv_or_DOI_string = factory.lazy_attribute(lambda o: o.pub_DOI)
