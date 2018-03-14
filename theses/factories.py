import factory

from common.helpers.factories import FormFactory
from journals.constants import SCIPOST_JOURNALS_DOMAINS
from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.models import Contributor

from .models import ThesisLink
from .forms import VetThesisLinkForm
from .constants import THESIS_TYPES


class ThesisLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ThesisLink

    requested_by = factory.Iterator(Contributor.objects.all())
    type = factory.Iterator(THESIS_TYPES, getter=lambda c: c[0])
    domain = factory.Iterator(SCIPOST_JOURNALS_DOMAINS, getter=lambda c: c[0])
    discipline = factory.Iterator(SCIPOST_DISCIPLINES, getter=lambda c: c[0])
    subject_area = factory.Iterator(SCIPOST_SUBJECT_AREAS[0][1], getter=lambda c: c[0])
    title = factory.Faker('text')
    pub_link = factory.Faker('uri')
    author = factory.Faker('name')
    supervisor = factory.Faker('name')
    institution = factory.Faker('company')
    defense_date = factory.Faker('date')
    abstract = factory.Faker('paragraph')


class VettedThesisLinkFactory(ThesisLinkFactory):
    vetted_by = factory.Iterator(Contributor.objects.all())
    vetted = True


class VetThesisLinkFormFactory(FormFactory):
    class Meta:
        model = VetThesisLinkForm

    action_option = VetThesisLinkForm.ACCEPT
