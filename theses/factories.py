__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from common.helpers.factories import FormFactory
from journals.constants import SCIPOST_JOURNALS_DOMAINS
from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.models import Contributor

from .models import ThesisLink
from .forms import VetThesisLinkForm
from .constants import THESIS_TYPES


class BaseThesisLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ThesisLink
        abstract = True

    requested_by = factory.Iterator(Contributor.objects.all())
    vetted_by = factory.Iterator(Contributor.objects.all())
    vetted = True

    type = factory.Iterator(THESIS_TYPES, getter=lambda c: c[0])
    domain = factory.Iterator(SCIPOST_JOURNALS_DOMAINS, getter=lambda c: c[0])
    discipline = factory.Iterator(SCIPOST_DISCIPLINES, getter=lambda c: c[0])
    subject_area = factory.Iterator(SCIPOST_SUBJECT_AREAS[0][1], getter=lambda c: c[0])
    title = factory.Faker('sentence')
    pub_link = factory.Faker('uri')
    author = factory.Faker('name')
    supervisor = factory.Faker('name')
    institution = factory.Faker('company')
    defense_date = factory.Faker('date_this_decade')
    abstract = factory.Faker('paragraph')

    @factory.post_generation
    def author_as_cont(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for contributor in extracted:
                self.author_as_cont.add(contributor)
        elif factory.Faker('boolean'):
            contributor = Contributor.objects.order_by('?').first()
            self.author_as_cont.add(contributor)


class ThesisLinkFactory(BaseThesisLinkFactory):
    pass


class VetThesisLinkFormFactory(FormFactory):
    class Meta:
        model = VetThesisLinkForm

    action_option = VetThesisLinkForm.ACCEPT
