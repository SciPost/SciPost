__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase

from scipost.factories import ContributorFactory
from ..factories import *


class TestMailingListFactory(TestCase):
    def test_can_create_mailing_lists(self):
        mailing_list = MailingListFactory()
        self.assertIsNotNone(mailing_list)

    def test_can_subscribe_contributor(self):
        contributor = ContributorFactory()
        mailing_list = MailingListFactory()
        mailing_list.add_eligible_subscriber(contributor)

        self.assertEqual(mailing_list.eligible_subscribers.count(), 1)
        self.assertEqual(mailing_list.subscribed.count(), 1)
        self.assertEqual(mailing_list.email_list, [contributor.profile.email])

    def test_can_unsubscribe_contributor(self):
        contributor = ContributorFactory()
        mailing_list = MailingListFactory()

        mailing_list.add_eligible_subscriber(contributor)
        mailing_list.unsubscribe(contributor)

        self.assertEqual(mailing_list.eligible_subscribers.count(), 1)
        self.assertEqual(mailing_list.subscribed.count(), 0)
        self.assertEqual(mailing_list.email_list, [])

    def test_does_not_automatically_subscribe_if_opt_in(self):
        contributor = ContributorFactory()
        mailing_list = MailingListFactory(is_opt_in=True)
        mailing_list.add_eligible_subscriber(contributor)

        self.assertEqual(mailing_list.eligible_subscribers.count(), 1)
        self.assertEqual(mailing_list.subscribed.count(), 0)
        self.assertEqual(mailing_list.email_list, [])

    def test_does_not_include_nonprimary_emails(self):
        contributor = ContributorFactory()
        mailing_list = MailingListFactory()
        mailing_list.add_eligible_subscriber(contributor)

        self.assertEqual(mailing_list.email_list, [contributor.profile.email])
