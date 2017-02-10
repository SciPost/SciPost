import factory

from django.test import TestCase

from scipost.factories import ContributorFactory
from .factories import ThesisLinkFactory, VetThesisLinkFormFactory
from .forms import RequestThesisLinkForm, VetThesisLinkForm
from common.helpers import model_form_data


class TestRequestThesisLink(TestCase):
    fixtures = ['permissions', 'groups']

    def setUp(self):
        self.contributor = ContributorFactory()
        self.user = self.contributor.user
        self.valid_form_data = model_form_data(
            ThesisLinkFactory(), RequestThesisLinkForm, form_kwargs={'user': self.user})

    def test_valid_data_is_valid(self):
        form_data = self.valid_form_data
        form = RequestThesisLinkForm(self.valid_form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_data_without_user_is_not_valid(self):
        form_data = self.valid_form_data
        with self.assertRaises(KeyError):
            RequestThesisLinkForm(self.valid_form_data)

    def test_empty_domain_is_invalid(self):
        form_data = self.valid_form_data
        form_data['domain'] = ''
        form = RequestThesisLinkForm(form_data, user=self.user)
        self.assertEqual(form.errors['domain'], ['This field is required.'])

    def test_thesislink_is_requested_by_correct_contributor(self):
        form_data = self.valid_form_data
        contributor = ContributorFactory()
        form = RequestThesisLinkForm(form_data, user=contributor.user)

        # Check if the user is properly saved to the new ThesisLink as `requested_by`
        thesislink = form.save()
        self.assertEqual(thesislink.requested_by, contributor)
