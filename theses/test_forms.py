import factory

from django.test import TestCase

from .factories import ThesisLinkFactory, VetThesisLinkFormFactory
from .forms import RequestThesisLinkForm, VetThesisLinkForm
from common.helpers import model_form_data


class TestRequestThesisLink(TestCase):
    fixtures = ['permissions', 'groups']

    def setUp(self):
        self.valid_form_data = model_form_data(ThesisLinkFactory(), RequestThesisLinkForm)

    def test_valid_data_is_valid(self):
        form_data = self.valid_form_data
        form = RequestThesisLinkForm(self.valid_form_data)
        self.assertTrue(form.is_valid())

    def test_empty_domain_is_invalid(self):
        form_data = self.valid_form_data
        form_data['domain'] = ''
        form = RequestThesisLinkForm(form_data)
        form.is_valid()
        self.assertEqual(form.errors['domain'], ['This field is required.'])


class TestVetThesisLinkRequests(TestCase):
    fixtures = ['permissions', 'groups']

    def test_thesislink_gets_vetted_when_accepted(self):
        thesis_link = ThesisLinkFactory()
        form = VetThesisLinkFormFactory()
        form.is_valid()
        form.vet_request(thesis_link)
        self.assertTrue(thesis_link.vetted)

    def test_thesislink_is_not_vetted_when_refused(self):
        thesis_link = ThesisLinkFactory()
        form = VetThesisLinkFormFactory(action_option=VetThesisLinkForm.REFUSE)
        form.is_valid()
        form.vet_request(thesis_link)
        self.assertFalse(thesis_link.vetted)
