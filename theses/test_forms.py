import factory

from django.test import TestCase

from .factories import ThesisLinkFactory
from .forms import RequestThesisLinkForm
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
