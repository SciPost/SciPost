import factory

from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.factories import ContributorFactory
from scipost.models import Contributor
from journals.constants import SCIPOST_JOURNALS_DOMAINS
from common.helpers import random_arxiv_identifier_with_version_number, random_external_doi

from .constants import COMMENTARY_TYPES
from .models import Commentary

from faker import Faker


class CommentaryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Commentary

    requested_by = factory.SubFactory(ContributorFactory)
    type = factory.Iterator(COMMENTARY_TYPES, getter=lambda c: c[0])
    discipline = factory.Iterator(SCIPOST_DISCIPLINES, getter=lambda c: c[0])
    domain = factory.Iterator(SCIPOST_JOURNALS_DOMAINS, getter=lambda c: c[0])
    subject_area = factory.Iterator(SCIPOST_SUBJECT_AREAS[0][1], getter=lambda c: c[0])
    pub_title = factory.Faker('text')
    pub_DOI = factory.Sequence(lambda n: random_external_doi())
    arxiv_identifier = factory.Sequence(lambda n: random_arxiv_identifier_with_version_number())
    arxiv_link = factory.Faker('uri')
    pub_abstract = factory.lazy_attribute(lambda x: Faker().paragraph())

    @factory.post_generation
    def arxiv_link(self, create, extracted, **kwargs):
        self.arxiv_link = 'https://arxiv.org/abs/%s' % self.arxiv_identifier
        self.arxiv_or_DOI_string = self.arxiv_identifier

    @factory.post_generation
    def create_urls(self, create, extracted, **kwargs):
        self.parse_links_into_urls(commit=create)

    @factory.post_generation
    def add_authors(self, create, extracted, **kwargs):
        contributors = list(Contributor.objects.order_by('?')
                            .exclude(pk=self.requested_by.pk).all()[:4])
        for contrib in contributors:
            self.author_list += ', %s %s' % (contrib.user.first_name, contrib.user.last_name)
            if create:
                self.authors.add(contrib)


class VettedCommentaryFactory(CommentaryFactory):
    vetted = True
    vetted_by = factory.SubFactory(ContributorFactory)


class UnpublishedVettedCommentaryFactory(VettedCommentaryFactory):
    pub_DOI = ''


class UnvettedCommentaryFactory(CommentaryFactory):
    vetted = False
