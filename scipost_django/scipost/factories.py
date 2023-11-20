__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import pytz

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from journals.models.publication import Publication
from profiles.factories import ProfileFactory
from submissions.models.submission import Submission

from .constants import NORMAL_CONTRIBUTOR
from .models import *
from common.faker import LazyRandEnum, fake


class ContributorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contributor
        django_get_or_create = ("user",)

    user = factory.SubFactory("scipost.factories.UserFactory", contributor=None)
    profile = factory.RelatedFactory(
        ProfileFactory,
        first_name=factory.SelfAttribute("..user.first_name"),
        last_name=factory.SelfAttribute("..user.last_name"),
        factory_related_name="contributor",
    )
    invitation_key = factory.Faker("md5")
    activation_key = factory.Faker("md5")
    key_expires = factory.Faker("future_datetime", tzinfo=pytz.utc)
    status = NORMAL_CONTRIBUTOR  # normal user
    address = factory.Faker("address")

    @classmethod
    def from_profile(cls, profile):
        contributor = cls(
            user__first_name=profile.first_name,
            user__last_name=profile.last_name,
        )
        contributor.profile = profile
        contributor.save()
        return contributor


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
        django_get_or_create = ("username",)

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


class GroupFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")

    class Meta:
        model = Group


class TOTPDeviceFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory("scipost.factories.UserFactory")
    name = factory.Faker("pystr")
    token = factory.LazyFunction(lambda: fake.md5()[:16])

    class Meta:
        model = TOTPDevice
        django_get_or_create = ("user", "name")


class SubmissionRemarkFactory(factory.django.DjangoModelFactory):
    contributor = factory.SubFactory(ContributorFactory)
    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    date = factory.Faker("date_time_this_decade")
    remark = factory.Faker("paragraph")

    class Meta:
        model = Remark


class UnavailabilityPeriodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UnavailabilityPeriod

    contributor = factory.SubFactory(ContributorFactory)
    start = factory.Faker("date_time_this_decade")
    end = factory.LazyAttribute(
        lambda self: fake.aware.date_between(start_date=self.start, end_date="+1y")
    )


class AuthorshipClaimFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuthorshipClaim

    claimant = factory.SubFactory(ContributorFactory)
    status = LazyRandEnum(AUTHORSHIP_CLAIM_STATUS)
    vetted_by = factory.LazyAttribute(
        lambda self: VettingEditorFactory() if self.status != 0 else None
    )


class CitationNotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CitationNotification

    class Params:
        item = None

    contributor = factory.SubFactory(ContributorFactory)
    processed = factory.Faker("boolean")
    cited_in_submission = factory.LazyAttribute(
        lambda self: self.item if isinstance(self.item, Submission) else None
    )
    cited_in_publication = factory.LazyAttribute(
        lambda self: self.item if isinstance(self.item, Publication) else None
    )
