__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

import factory
from django.utils.text import slugify

from colleges.models.nomination import (
    FellowshipInvitation,
    FellowshipNomination,
    FellowshipNominationComment,
    FellowshipNominationDecision,
    FellowshipNominationEvent,
    FellowshipNominationVote,
    FellowshipNominationVotingRound,
)
from common.faker import LazyAwareDate, LazyAwareDateOffset, LazyRandEnum, fake
from ontology.factories import AcademicFieldFactory
from profiles.factories import ProfileFactory
from scipost.factories import ContributorFactory
from scipost.models import Contributor

from .models import College, Fellowship


############
# Colleges #
############


class CollegeFactory(factory.django.DjangoModelFactory):
    name = factory.SelfAttribute("acad_field.name")
    acad_field = factory.SubFactory(AcademicFieldFactory)
    slug = factory.LazyAttribute(lambda self: slugify(self.name))
    order = factory.Sequence(lambda n: n + 1)

    class Meta:
        model = College
        django_get_or_create = ("name",)


###############
# Fellowships #
###############


class BaseFellowshipFactory(factory.django.DjangoModelFactory):
    college = factory.SubFactory(CollegeFactory)
    contributor = factory.SubFactory(
        ContributorFactory,
        profile__acad_field=factory.SelfAttribute("...college.acad_field"),
    )
    start_date = fake.aware.date_time_this_year()
    until_date = factory.LazyAttribute(
        lambda self: self.start_date + datetime.timedelta(days=5 * 365)
    )

    class Meta:
        model = Fellowship
        django_get_or_create = ("contributor", "college")
        abstract = True


class FellowshipFactory(BaseFellowshipFactory):
    status = "regular"


class GuestFellowshipFactory(BaseFellowshipFactory):
    status = "guest"


class SeniorFellowshipFactory(BaseFellowshipFactory):
    status = "senior"

class FellowFactory(ContributorFactory):

    @factory.post_generation
    def fellowship(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.fellowship = extracted
        else:
            self.fellowship = FellowshipFactory(
                contributor=self,
                college=CollegeFactory(acad_field=self.profile.acad_field),
            )

###############
# Nominations #
###############


class FellowshipNominationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FellowshipNomination

    college = factory.SubFactory(CollegeFactory)
    profile = factory.SubFactory(ProfileFactory)
    nominated_by = factory.SubFactory(ContributorFactory)
    nominated_on = LazyAwareDate("date_time_this_year")
    nominator_comments = factory.Faker("text")
    fellowship = None


class EmptyRoundFellowshipNominationFactory(FellowshipNominationFactory):
    @factory.post_generation
    def create_voting_round(self, create, extracted, **kwargs):
        if not create:
            return
        self.voting_round = FellowshipNominationVotingRoundFactory(nomination=self)
        self.voting_round.save()


class RegisteredFellowshipNominationFactory(FellowshipNominationFactory):
    @factory.post_generation
    def create_profile_contributor(self, create, extracted, **kwargs):
        if not create:
            return
        self.profile.contributor = ContributorFactory(profile=self.profile)
        self.profile.save()


class SuccessfulFellowshipNominationFactory(RegisteredFellowshipNominationFactory):
    @factory.post_generation
    def fellowship(self, create, extracted, **kwargs):
        if not create:
            return
        self.fellowship = FellowshipFactory(
            contributor=self.profile.contributor, college=self.college
        )
        self.fellowship.save()


class FellowshipNominationEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FellowshipNominationEvent

    nomination = factory.SubFactory(FellowshipNominationFactory)
    description = factory.Faker("text")
    by = factory.SubFactory(ContributorFactory)
    on = LazyAwareDate("date_time_this_year")


class FellowshipNominationCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FellowshipNominationComment

    nomination = factory.SubFactory(FellowshipNominationFactory)
    text = factory.Faker("text")
    by = factory.SubFactory(ContributorFactory)
    on = LazyAwareDate("date_time_this_year")


class FellowshipNominationVotingRoundFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FellowshipNominationVotingRound

    nomination = factory.SubFactory(FellowshipNominationFactory)
    voting_opens = LazyAwareDate("date_time_this_year")
    voting_deadline = LazyAwareDateOffset("voting_opens", "+14d")

    @factory.post_generation
    def eligible_to_vote(self, create, extracted, **kwargs):
        if not create:
            # TODO: Eventually should use a method in the object itself,
            # right now this is part of the view and I don't want to couple them
            return
        if extracted:
            self.eligible_to_vote.set(extracted)
            self.save()


class FellowshipNominationVoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FellowshipNominationVote
        django_get_or_create = ("voting_round", "fellow")

    voting_round = factory.SubFactory(FellowshipNominationVotingRoundFactory)
    fellow = factory.SubFactory(FellowshipFactory)
    vote = LazyRandEnum(FellowshipNominationVote.VOTE_CHOICES)
    on = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.voting_round.voting_opens,
            end_date=self.voting_round.voting_deadline,
        )
    )


class FellowshipNominationDecisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FellowshipNominationDecision
        django_get_or_create = ("voting_round",)

    voting_round = factory.SubFactory(FellowshipNominationVotingRoundFactory)
    outcome = LazyRandEnum(FellowshipNominationDecision.OUTCOME_CHOICES)
    comments = factory.Faker("text")
    fixed_on = LazyAwareDateOffset("voting_round.voting_deadline", "+1y")


class FellowshipInvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FellowshipInvitation

    nomination = factory.SubFactory(FellowshipNominationFactory)
    invited_on = LazyAwareDate("date_time_this_year")
    response = LazyRandEnum(FellowshipInvitation.RESPONSE_CHOICES)
    comments = factory.Faker("text")
