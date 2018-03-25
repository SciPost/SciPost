__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import random

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from common.helpers import generate_orcid
from submissions.models import Submission

from .models import Contributor, EditorialCollege, EditorialCollegeFellowship, Remark
from .constants import TITLE_CHOICES, SCIPOST_SUBJECT_AREAS


class ContributorFactory(factory.django.DjangoModelFactory):
    title = factory.Iterator(TITLE_CHOICES, getter=lambda c: c[0])
    user = factory.SubFactory('scipost.factories.UserFactory', contributor=None)
    status = 1  # normal user
    vetted_by = factory.Iterator(Contributor.objects.all())
    personalwebpage = factory.Faker('uri')
    expertises = factory.Iterator(SCIPOST_SUBJECT_AREAS[0][1], getter=lambda c: [c[0]])
    orcid_id = factory.lazy_attribute(lambda n: generate_orcid())
    address = factory.Faker('address')
    invitation_key = factory.Faker('md5')
    activation_key = factory.Faker('md5')
    key_expires = factory.Faker('future_datetime')

    class Meta:
        model = Contributor
        django_get_or_create = ('user',)

    @factory.post_generation
    def add_to_vetting_editors(self, create, extracted, **kwargs):
        if create:
            from affiliations.factories import AffiliationFactory
            AffiliationFactory(contributor=self)


class VettingEditorFactory(ContributorFactory):
    @factory.post_generation
    def add_to_vetting_editors(self, create, extracted, **kwargs):
        if not create:
            return
        self.user.groups.add(Group.objects.get(name="Vetting Editors"))


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker('user_name')
    password = factory.PostGenerationMethodCall('set_password', 'adm1n')
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    # When user object is created, associate new Contributor object to it.
    contributor = factory.RelatedFactory(ContributorFactory, 'user')

    class Meta:
        model = get_user_model()

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        # If the object is not saved, we cannot use many-to-many relationship.
        if not create:
            return
        # If group objects were passed in, use those.
        if extracted:
            for group in extracted:
                self.groups.add(group)
        else:
            self.groups.add(Group.objects.get(name="Registered Contributors"))


class EditorialCollegeFactory(factory.django.DjangoModelFactory):
    discipline = random.choice(['Physics', 'Chemistry', 'Medicine'])

    class Meta:
        model = EditorialCollege
        django_get_or_create = ('discipline',)


class EditorialCollegeFellowshipFactory(factory.django.DjangoModelFactory):
    college = factory.Iterator(EditorialCollege.objects.all())
    contributor = factory.Iterator(Contributor.objects.exclude(
                                   user__username='deleted').order_by('?'))

    class Meta:
        model = EditorialCollegeFellowship


class SubmissionRemarkFactory(factory.django.DjangoModelFactory):
    contributor = factory.Iterator(Contributor.objects.all())
    submission = factory.Iterator(Submission.objects.all())
    date = factory.Faker('date_time_this_decade')
    remark = factory.Faker('paragraph')

    class Meta:
        model = Remark
