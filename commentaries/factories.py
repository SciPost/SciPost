import factory

from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.models import Contributor
from journals.constants import SCIPOST_JOURNALS_DOMAINS
from common.helpers import random_arxiv_identifier_with_version_number, random_external_doi

from .constants import COMMENTARY_TYPES
from .models import Commentary


class BaseCommentaryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Commentary
        django_get_or_create = ('pub_DOI', 'arxiv_identifier')
        abstract = True

    requested_by = factory.Iterator(Contributor.objects.all())
    vetted = True
    vetted_by = factory.Iterator(Contributor.objects.all())
    type = factory.Iterator(COMMENTARY_TYPES, getter=lambda c: c[0])
    discipline = factory.Iterator(SCIPOST_DISCIPLINES, getter=lambda c: c[0])
    domain = factory.Iterator(SCIPOST_JOURNALS_DOMAINS, getter=lambda c: c[0])
    subject_area = factory.Iterator(SCIPOST_SUBJECT_AREAS[0][1], getter=lambda c: c[0])
    title = factory.Faker('sentence')
    pub_DOI = factory.Sequence(lambda n: random_external_doi())
    arxiv_identifier = factory.Sequence(lambda n: random_arxiv_identifier_with_version_number('1'))
    author_list = factory.Faker('name')
    pub_abstract = factory.Faker('text')
    pub_date = factory.Faker('date_this_decade')
    pub_abstract = factory.Faker('paragraph')

    arxiv_link = factory.lazy_attribute(lambda o: 'https://arxiv.org/abs/%s' % o.arxiv_identifier)
    arxiv_or_DOI_string = factory.lazy_attribute(lambda o: (
        o.arxiv_identifier if o.arxiv_identifier else o.pub_DOI))

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
    arxiv_link = ''
    arxiv_or_DOI_string = factory.lazy_attribute(lambda o: o.pub_DOI)
