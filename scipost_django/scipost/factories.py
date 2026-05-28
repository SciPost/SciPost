__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re

import factory
import pytz

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from common.utils.text import latinise
from journals.models.publication import Publication
from profiles.factories import ProfileFactory
from submissions.models.submission import Submission

from .constants import NORMAL_CONTRIBUTOR
from .models import *
from common.faker import LazyAwareDateOffset, LazyRandEnum, fake


class ContributorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contributor
        django_get_or_create = ("dbuser",)

    profile = factory.SubFactory(ProfileFactory)
    dbuser = factory.SubFactory(
        "scipost.factories.UserFactory",
        first_name=factory.SelfAttribute("..profile.first_name"),
        last_name=factory.SelfAttribute("..profile.last_name"),
    )
    invitation_key = factory.Faker("md5")
    activation_key = factory.Faker("md5")
    key_expires = factory.Faker("future_datetime", tzinfo=pytz.utc)
    status = NORMAL_CONTRIBUTOR  # normal user
    address = factory.Faker("address")

    @factory.post_generation
    def email(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.dbuser.email = extracted
            profile_email = self.profile.emails.first()
            profile_email.email = extracted
            profile_email.save()
            self.dbuser.save()
        else:
            self.dbuser.email = self.profile.emails.first().email
            self.dbuser.save()


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
        lambda self: "{first_name[0]}{last_name}".format(
            first_name=re.sub(r"[\W\s]", "", latinise(self.first_name.lower())),
            last_name=re.sub(r"[\W\s]", "", latinise(self.last_name.lower())),
        )
    )
    is_active = True
    class Meta:
        model = get_user_model()
        django_get_or_create = ("username",)

    @factory.post_generation
    def email(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.email = extracted
        else:
            self.email = f"{self.username}@example.com"

        self.save()

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            password = extracted
        else:
            password = f"{self.username}_pass"

        self.set_password(password)
        self.save()

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
    end = LazyAwareDateOffset("start", "+1y")


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
