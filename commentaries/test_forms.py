import factory

from django.test import TestCase

from scipost.factories import UserFactory

from .factories import VettedCommentaryFactory
from .forms import RequestCommentaryForm
from common.helpers import model_form_data


class TestRequestCommentaryForm(TestCase):
    fixtures = ['permissions', 'groups']

    def setUp(self):
        factory_instance = VettedCommentaryFactory.build()
        self.user = UserFactory()
        self.valid_form_data = model_form_data(factory_instance, RequestCommentaryForm)

    def test_valid_data_is_valid_for_arxiv(self):
        """Test valid form for Arxiv identifier"""
        form_data = self.valid_form_data
        form_data['pub_DOI'] = ''
        form = RequestCommentaryForm(form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_valid_data_is_valid_for_DOI(self):
        """Test valid form for DOI"""
        form_data = self.valid_form_data
        form_data['arxiv_identifier'] = ''
        form = RequestCommentaryForm(form_data, user=self.user)
        self.assertTrue(form.is_valid())

    # def test_form_has_no_identifiers(self):
    #     """Test invalid form has no DOI nor Arxiv ID"""
    #     form_data = self.valid_form_data
    #     form_data['pub_DOI'] = ''
    #     form_data['arxiv_identifier'] = ''
    #     form = RequestCommentaryForm(form_data, user=self.user)
    #     form_response = form.is_valid()
    #     print(form_response)
    #     self.assertFormError(form_response, form, 'arxiv_identifier', None)
