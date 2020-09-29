__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import pytz

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from common.helpers import generate_orcid
from submissions.models import Submission

from .models import Contributor, Remark, TOTPDevice
from .constants import TITLE_CHOICES, NORMAL_CONTRIBUTOR


class ContributorFactory(factory.django.DjangoModelFactory):
    profile = factory.SubFactory('profiles.factories.ProfileFactory')
    user = factory.SubFactory('scipost.factories.UserFactory', contributor=None)
    invitation_key = factory.Faker('md5')
    activation_key = factory.Faker('md5')
    key_expires = factory.Faker('future_datetime', tzinfo=pytz.utc)
    status = NORMAL_CONTRIBUTOR  # normal user
    title = factory.Iterator(TITLE_CHOICES, getter=lambda c: c[0])
    orcid_id = factory.lazy_attribute(lambda n: generate_orcid())
    address = factory.Faker('address')
    personalwebpage = factory.Faker('uri')
    # vetted_by = factory.Iterator(Contributor.objects.all())

    class Meta:
        model = Contributor
        django_get_or_create = ('user',)


class VettingEditorFactory(ContributorFactory):
    @factory.post_generation
    def add_to_vetting_editors(self, create, extracted, **kwargs):
        if not create:
            return
        self.user.groups.add(Group.objects.get_or_create(name="Vetting Editors")[0])


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker('user_name')
    password = factory.PostGenerationMethodCall('set_password', 'adm1n')
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

    # When user object is created, associate new Contributor object to it.
    contrib = factory.RelatedFactory(ContributorFactory, 'user')

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
            self.groups.add(Group.objects.get_or_create(name="Registered Contributors")[0])


class TOTPDeviceFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory('scipost.factories.UserFactory')
    name = factory.Faker('pystr')
    token = factory.Faker('md5')

    class Meta:
        model = TOTPDevice


class SubmissionRemarkFactory(factory.django.DjangoModelFactory):
    contributor = factory.Iterator(Contributor.objects.all())
    submission = factory.Iterator(Submission.objects.all())
    date = factory.Faker('date_time_this_decade')
    remark = factory.Faker('paragraph')

    class Meta:
        model = Remark
