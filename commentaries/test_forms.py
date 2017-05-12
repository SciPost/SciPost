import re

from django.test import TestCase

from common.helpers import model_form_data
from scipost.factories import UserFactory

from .factories import VettedCommentaryFactory, UnvettedCommentaryFactory
from .forms import RequestCommentaryForm, VetCommentaryForm, DOIToQueryForm
from .models import Commentary
from common.helpers.test import add_groups_and_permissions


class TestDOIToQueryForm(TestCase):
    def setUp(self):
        add_groups_and_permissions()

    def test_invalid_doi_is_invalid(self):
        invalid_data = {'doi': 'blablab'}
        form = DOIToQueryForm(invalid_data)
        self.assertFalse(form.is_valid())

    def test_doi_that_already_has_commentary_page_is_invalid(self):
        unvetted_commentary = UnvettedCommentaryFactory()
        invalid_data = {'doi': unvetted_commentary.pub_DOI}
        form = DOIToQueryForm(invalid_data)
        self.assertFalse(form.is_valid())
        error_message = form.errors['doi'][0]
        self.assertRegexpMatches(error_message, re.compile('already exist'))

    def test_physrev_doi_is_valid(self):
        physrev_doi = "10.21468/SciPostPhys.2.2.010"
        form = DOIToQueryForm({'doi': physrev_doi})
        self.assertTrue(form.is_valid())

    def test_scipost_doi_is_valid(self):
        scipost_doi = "10.21468/SciPostPhys.2.2.010"
        form = DOIToQueryForm({'doi': scipost_doi})
        self.assertTrue(form.is_valid())

    def test_old_doi_is_valid(self):
        old_doi = "10.1088/0022-3719/7/6/005"
        form = DOIToQueryForm({'doi': old_doi})
        self.assertTrue(form.is_valid())

    def test_valid_but_nonexistent_doi_is_invalid(self):
        doi = "10.21468/NonExistentJournal.2.2.010"
        form = DOIToQueryForm({'doi': doi})
        self.assertEqual(form.is_valid(), False)


class TestVetCommentaryForm(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.commentary = UnvettedCommentaryFactory.create()
        self.user = UserFactory()
        self.form_data = {
            'action_option': VetCommentaryForm.ACTION_ACCEPT,
            'refusal_reason': VetCommentaryForm.REFUSAL_EMPTY,
            'email_response_field': 'Lorem Ipsum'
        }


    def test_valid_accepted_form(self):
        """Test valid form data and return Commentary"""
        form = VetCommentaryForm(self.form_data, commentary_id=self.commentary.id, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertFalse(Commentary.objects.vetted().exists())
        self.assertTrue(Commentary.objects.awaiting_vetting().exists())

        # Accept Commentary in database
        form.process_commentary()
        self.assertTrue(Commentary.objects.vetted().exists())
        self.assertFalse(Commentary.objects.awaiting_vetting().exists())

    def test_valid_modified_form(self):
        """Test valid form data and delete Commentary"""
        self.form_data['action_option'] = VetCommentaryForm.ACTION_MODIFY
        form = VetCommentaryForm(self.form_data, commentary_id=self.commentary.id, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertFalse(Commentary.objects.vetted().exists())
        self.assertTrue(Commentary.objects.awaiting_vetting().exists())

        # Delete the Commentary
        form.process_commentary()
        self.assertTrue(form.commentary_is_modified())
        self.assertFalse(Commentary.objects.awaiting_vetting().exists())

    def test_valid_rejected_form(self):
        """Test valid form data and delete Commentary"""
        self.form_data['action_option'] = VetCommentaryForm.ACTION_REFUSE
        self.form_data['refusal_reason'] = VetCommentaryForm.REFUSAL_UNTRACEBLE
        form = VetCommentaryForm(self.form_data, commentary_id=self.commentary.id, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertFalse(Commentary.objects.vetted().exists())
        self.assertTrue(Commentary.objects.awaiting_vetting().exists())

        # Delete the Commentary
        form.process_commentary()
        self.assertTrue(form.commentary_is_refused())
        self.assertFalse(Commentary.objects.awaiting_vetting().exists())

        # Refusal choice is ok
        refusal_reason_inserted = VetCommentaryForm.COMMENTARY_REFUSAL_DICT[
            VetCommentaryForm.REFUSAL_UNTRACEBLE]
        self.assertEqual(form.get_refusal_reason(), refusal_reason_inserted)

    def test_process_before_validation(self):
        """Test response of form on processing before validation"""
        form = VetCommentaryForm(self.form_data, commentary_id=self.commentary.id, user=self.user)
        self.assertRaises(ValueError, form.process_commentary)


class TestRequestCommentaryForm(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        factory_instance = UnvettedCommentaryFactory.build()
        self.user = UserFactory()
        self.valid_form_data = model_form_data(factory_instance, RequestCommentaryForm)

    def empty_and_return_form_data(self, key):
        """Empty specific valid_form_data field and return"""
        self.valid_form_data[key] = None
        return self.valid_form_data

    def test_valid_data_is_valid_for_arxiv(self):
        """Test valid form for Arxiv identifier"""
        form_data = self.valid_form_data
        form_data['pub_DOI'] = ''
        form = RequestCommentaryForm(form_data, user=self.user)
        self.assertTrue(form.is_valid())

        # Check if the user is properly saved to the new Commentary as `requested_by`
        commentary = form.save()
        self.assertTrue(commentary.requested_by)

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

    def test_form_with_duplicate_DOI(self):
        """Test form response with already existing DOI"""
        # Create a factory instance containing Arxiv ID and DOI
        VettedCommentaryFactory.create()

        # Test duplicate DOI entry
        form_data = self.empty_and_return_form_data('arxiv_identifier')
        form = RequestCommentaryForm(form_data, user=self.user)
        self.assertTrue('pub_DOI' in form.errors)
        self.assertFalse(form.is_valid())

        # Check is existing commentary is valid
        existing_commentary = form.get_existing_commentary()
        self.assertEqual(existing_commentary.pub_DOI, form_data['pub_DOI'])

    def test_form_with_duplicate_arxiv_id(self):
        """Test form response with already existing Arxiv ID"""
        VettedCommentaryFactory.create()

        # Test duplicate Arxiv entry
        form_data = self.empty_and_return_form_data('pub_DOI')
        form = RequestCommentaryForm(form_data, user=self.user)
        self.assertTrue('arxiv_identifier' in form.errors)
        self.assertFalse(form.is_valid())

        # Check is existing commentary is valid
        existing_commentary = form.get_existing_commentary()
        self.assertEqual(existing_commentary.arxiv_identifier, form_data['arxiv_identifier'])
