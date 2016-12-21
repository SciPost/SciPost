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

    def test_form_has_no_identifiers(self):
        """Test invalid form has no DOI nor Arxiv ID"""
        form_data = self.valid_form_data
        form_data['pub_DOI'] = ''
        form_data['arxiv_identifier'] = ''
        form = RequestCommentaryForm(form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue('arxiv_identifier' in form.errors)
        self.assertTrue('pub_DOI' in form.errors)

    def test_form_with_duplicate_identifiers(self):
        """Test form response with already existing identifiers"""
        # Create a factory instance containing Arxiv ID and DOI
        VettedCommentaryFactory.create()

        # Test duplicate DOI entry
        form_data = self.valid_form_data
        form_data['arxiv_identifier'] = ''
        form = RequestCommentaryForm(form_data, user=self.user)
        self.assertTrue('pub_DOI' in form.errors)
        self.assertFalse(form.is_valid())

        # Test duplicate Arxiv entry
        form_data = self.valid_form_data
        form_data['pub_DOI'] = ''
        form = RequestCommentaryForm(form_data, user=self.user)
        self.assertTrue('arxiv_identifier' in form.errors)
        self.assertFalse(form.is_valid())
