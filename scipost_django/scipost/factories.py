__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import pytz

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from profiles.factories import ProfileFactory

from .constants import NORMAL_CONTRIBUTOR
from .models import Contributor, Remark, TOTPDevice
from common.faker import fake


class ContributorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contributor
        django_get_or_create = ("user",)

    user = factory.SubFactory("scipost.factories.UserFactory", contributor=None)
    profile = factory.SubFactory(
        ProfileFactory,
        first_name=factory.SelfAttribute("..user.first_name"),
        last_name=factory.SelfAttribute("..user.last_name"),
    )
    invitation_key = factory.Faker("md5")
    activation_key = factory.Faker("md5")
    key_expires = factory.Faker("future_datetime", tzinfo=pytz.utc)
    status = NORMAL_CONTRIBUTOR  # normal user
    address = factory.Faker("address")

    @classmethod
    def from_profile(cls, profile):
        return cls(
            user__first_name=profile.first_name,
            user__last_name=profile.last_name,
        )


class VettingEditorFactory(ContributorFactory):
    @factory.post_generation
    def add_to_vetting_editors(self, create, extracted, **kwargs):
        if not create:
            return
        self.user.groups.add(Group.objects.get_or_create(name="Vetting Editors")[0])


class UserFactory(factory.django.DjangoModelFactory):
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.LazyAttribute(
        lambda self: "{first_char}{last_name}".format(
            first_char=self.first_name[0].lower(), last_name=self.last_name.lower()
        )
    )
    password = factory.PostGenerationMethodCall("set_password", "adm1n")
    email = factory.Faker("safe_email")
    is_active = True

    # When user object is created, associate new Contributor object to it.
    contrib = factory.RelatedFactory(ContributorFactory, "user")

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
            self.groups.add(
                Group.objects.get_or_create(name="Registered Contributors")[0]
            )


class TOTPDeviceFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory("scipost.factories.UserFactory")
    name = factory.Faker("pystr")
    token = factory.LazyFunction(lambda: fake.md5()[:16])

    class Meta:
        model = TOTPDevice


class SubmissionRemarkFactory(factory.django.DjangoModelFactory):
    contributor = factory.SubFactory(ContributorFactory)
    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    date = factory.Faker("date_time_this_decade")
    remark = factory.Faker("paragraph")

    class Meta:
        model = Remark
