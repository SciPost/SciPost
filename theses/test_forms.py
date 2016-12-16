import factory

from django.test import TestCase

from .factories import ThesisLinkFactory
from .forms import RequestThesisLinkForm


def valid_form_data(thesis_link):
    thesis_link_data = thesis_link.__dict__
    form_fields = list(RequestThesisLinkForm().fields.keys())
    return filter_keys(thesis_link_data, form_fields)


def filter_keys(dictionary, keys_to_keep):
    return {key: dictionary[key] for key in keys_to_keep}


class TestRequestThesisLink(TestCase):
    fixtures = ['permissions', 'groups']

    def test_valid_data_is_valid(self):
        thesis_data = valid_form_data(ThesisLinkFactory())
        form = RequestThesisLinkForm(thesis_data)
        self.assertTrue(form.is_valid())

    def test_empty_domain_is_invalid(self):
        thesis_data = valid_form_data(ThesisLinkFactory(domain=''))
        form = RequestThesisLinkForm(thesis_data)
        form.is_valid()
        self.assertEqual(form.errors['domain'], ['This field is required.'])
