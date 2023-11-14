__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase

from ..factories import (
    CollegeFactory,
    FellowshipFactory,
    FellowshipInvitationFactory,
    FellowshipNominationCommentFactory,
    FellowshipNominationDecisionFactory,
    FellowshipNominationEventFactory,
    FellowshipNominationFactory,
    FellowshipNominationVoteFactory,
    FellowshipNominationVotingRoundFactory,
    GuestFellowshipFactory,
    RegisteredFellowshipNominationFactory,
    SeniorFellowshipFactory,
    SuccessfulFellowshipNominationFactory,
)


class TestCollegeFactory(TestCase):
    def test_can_create_colleges(self):
        college = CollegeFactory()

        self.assertIsNotNone(college)


class TestFellowshipFactory(TestCase):
    def test_can_create_fellowships(self):
        fellowship = FellowshipFactory()

        self.assertIsNotNone(fellowship)
        self.assertEqual(fellowship.status, "regular")


class TestGuestFellowshipFactory(TestCase):
    def test_can_create_guest_fellowships(self):
        guest_fellowship = GuestFellowshipFactory()

        self.assertIsNotNone(guest_fellowship)
        self.assertEqual(guest_fellowship.status, "guest")


class TestSeniorFellowshipFactory(TestCase):
    def test_can_create_senior_fellowships(self):
        senior_fellowship = SeniorFellowshipFactory()

        self.assertIsNotNone(senior_fellowship)
        self.assertEqual(senior_fellowship.status, "senior")


class TestFellowshipNominationFactory(TestCase):
    def test_can_create_fellowship_nominations(self):
        fellowship_nomination = FellowshipNominationFactory()

        self.assertIsNotNone(fellowship_nomination)


class TestRegisteredFellowshipNominationFactory(TestCase):
    def test_can_create_registered_fellowship_nominations(self):
        registered_fellowship_nomination = RegisteredFellowshipNominationFactory()

        self.assertIsNotNone(registered_fellowship_nomination)
        self.assertIsNotNone(registered_fellowship_nomination.profile.contributor)


class TestSuccessfulFellowshipNominationFactory(TestCase):
    def test_can_create_successful_fellowship_nominations(self):
        successful_fellowship_nomination = SuccessfulFellowshipNominationFactory()

        self.assertIsNotNone(successful_fellowship_nomination)
        self.assertEqual(
            successful_fellowship_nomination.fellowship.contributor,
            successful_fellowship_nomination.profile.contributor,
        )
        self.assertEqual(
            successful_fellowship_nomination.fellowship.college,
            successful_fellowship_nomination.college,
        )


class TestFellowshipNominationEventFactory(TestCase):
    def test_can_create_fellowship_nomination_events(self):
        fellowship_nomination_event = FellowshipNominationEventFactory()

        self.assertIsNotNone(fellowship_nomination_event)


class TestFellowshipNominationCommentFactory(TestCase):
    def test_can_create_fellowship_nomination_comments(self):
        fellowship_nomination_comment = FellowshipNominationCommentFactory()

        self.assertIsNotNone(fellowship_nomination_comment)


class TestFellowshipNominationVotingRoundFactory(TestCase):
    def test_can_create_fellowship_nomination_voting_rounds(self):
        fellowship_nomination_voting_round = FellowshipNominationVotingRoundFactory()

        self.assertIsNotNone(fellowship_nomination_voting_round)


class TestFellowshipNominationVoteFactory(TestCase):
    def test_can_create_fellowship_nomination_votes(self):
        fellowship_nomination_vote = FellowshipNominationVoteFactory()

        self.assertIsNotNone(fellowship_nomination_vote)

    def test_nomination_vote_date_is_between_voting_round_open_period(self):
        fellowship_nomination_vote = FellowshipNominationVoteFactory()

        self.assertGreaterEqual(
            fellowship_nomination_vote.on,
            fellowship_nomination_vote.voting_round.voting_opens,
        )
        self.assertLessEqual(
            fellowship_nomination_vote.on,
            fellowship_nomination_vote.voting_round.voting_deadline,
        )


class TestFellowshipNominationDecisionFactory(TestCase):
    def test_can_create_fellowship_nomination_decisions(self):
        fellowship_nomination_decision = FellowshipNominationDecisionFactory()

        self.assertIsNotNone(fellowship_nomination_decision)


class TestFellowshipInvitationFactory(TestCase):
    def test_can_create_fellowship_invitations(self):
        fellowship_invitation = FellowshipInvitationFactory()
        self.assertIsNotNone(fellowship_invitation)
