__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re

from django.test import TestCase

from common.helpers import model_form_data
from scipost.factories import UserFactory, ContributorFactory

from ..factories import CommentaryFactory, UnvettedCommentaryFactory,\
                       UnvettedUnpublishedCommentaryFactory
from ..forms import RequestPublishedArticleForm, VetCommentaryForm, DOIToQueryForm,\
                   ArxivQueryForm, RequestArxivPreprintForm
from ..models import Commentary
from common.helpers import random_arxiv_identifier_with_version_number, random_external_doi
from common.helpers.test import add_groups_and_permissions


class TestArxivQueryForm(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        ContributorFactory.create_batch(5)

    def test_new_arxiv_identifier_is_valid(self):
        new_identifier_data = {'identifier': '1612.07611v1'}
        form = ArxivQueryForm(new_identifier_data)
        self.assertTrue(form.is_valid())

    def test_old_arxiv_identifier_is_valid(self):
        old_identifier_data = {'identifier': 'cond-mat/0612480v1'}
        form = ArxivQueryForm(old_identifier_data)
        self.assertTrue(form.is_valid())

    def test_invalid_arxiv_identifier(self):
        invalid_data = {'identifier': 'i am not valid'}
        form = ArxivQueryForm(invalid_data)
        self.assertFalse(form.is_valid())

    def test_new_arxiv_identifier_without_version_number_is_invalid(self):
        data = {'identifier': '1612.07611'}
        form = ArxivQueryForm(data)
        self.assertFalse(form.is_valid())

    def test_old_arxiv_identifier_without_version_number_is_invalid(self):
        data = {'identifier': 'cond-mat/0612480'}
        form = ArxivQueryForm(data)
        self.assertFalse(form.is_valid())

    def test_arxiv_identifier_that_already_has_commentary_page_is_invalid(self):
        unvetted_commentary = UnvettedCommentaryFactory()
        invalid_data = {'identifier': unvetted_commentary.arxiv_identifier}
        form = ArxivQueryForm(invalid_data)
        self.assertFalse(form.is_valid())
        error_message = form.errors['identifier'][0]
        self.assertRegex(error_message, re.compile('already exists'))

    def test_valid_but_non_existent_identifier_is_invalid(self):
        invalid_data = {'identifier': '1613.07611v1'}
        form = ArxivQueryForm(invalid_data)
        self.assertFalse(form.is_valid())


class TestDOIToQueryForm(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        ContributorFactory.create_batch(5)

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
        self.assertRegex(error_message, re.compile('already exists'))

    def test_physrev_doi_is_valid(self):
        physrev_doi = "10.1103/PhysRevLett.123.183602"
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
        ContributorFactory.create_batch(5)
        self.commentary = UnvettedCommentaryFactory.create()
        self.user = UserFactory.create()
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
        self.assertTrue(Commentary.objects.awaiting_vetting().count() == 1)

        # Modified Commentary in the database
        form.process_commentary()
        self.assertTrue(form.commentary_is_modified())
        self.assertTrue(Commentary.objects.awaiting_vetting().exists())

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
        self.assertRaises(AttributeError, form.process_commentary)


class TestRequestPublishedArticleForm(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        ContributorFactory.create_batch(5)
        factory_instance = UnvettedCommentaryFactory()
        self.user = UserFactory()
        self.valid_form_data = model_form_data(factory_instance, RequestPublishedArticleForm)
        self.valid_form_data['acad_field'] = factory_instance.acad_field.id
        self.valid_form_data['specialties'] = [s.id for s in factory_instance.specialties.all()]

    def test_valid_data_is_valid(self):
        """Test valid form for DOI"""
        form = RequestPublishedArticleForm({
            **self.valid_form_data,
            **{'pub_DOI': random_external_doi}
        })
        self.assertTrue(form.is_valid())

    def test_doi_that_already_has_commentary_page_is_invalid(self):
        unvetted_commentary = UnvettedCommentaryFactory()
        invalid_data = {**self.valid_form_data, **{'pub_DOI': unvetted_commentary.pub_DOI}}
        form = RequestPublishedArticleForm(invalid_data)
        self.assertEqual(form.is_valid(), False)
        error_message = form.errors['pub_DOI'][0]
        self.assertRegex(error_message, re.compile('already exists'))

    def test_commentary_without_pub_DOI_is_invalid(self):
        invalid_data = {**self.valid_form_data, **{'pub_DOI': ''}}
        form = RequestPublishedArticleForm(invalid_data)
        self.assertEqual(form.is_valid(), False)


class TestRequestArxivPreprintForm(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        ContributorFactory.create_batch(5)
        # Next line: don't use .build() because the instance must be saved so that
        # factory_instance.specialties.all() below works out.
        factory_instance = UnvettedUnpublishedCommentaryFactory()
        self.user = UserFactory()
        self.valid_form_data = model_form_data(factory_instance, RequestPublishedArticleForm)
        self.valid_form_data['arxiv_identifier'] = factory_instance.arxiv_identifier
        self.valid_form_data['acad_field'] = factory_instance.acad_field.id
        self.valid_form_data['specialties'] = [s.id for s in factory_instance.specialties.all()]

    def test_valid_data_is_valid(self):
        form = RequestArxivPreprintForm({
            **self.valid_form_data,
            **{'arxiv_identifier': random_arxiv_identifier_with_version_number}
        })
        print("form.errors:\n\t%s" % form.errors)
        self.assertTrue(form.is_valid())

    def test_identifier_that_already_has_commentary_page_is_invalid(self):
        commentary = UnvettedUnpublishedCommentaryFactory()
        invalid_data = {**self.valid_form_data, **{'arxiv_identifier': commentary.arxiv_identifier}}
        form = RequestArxivPreprintForm(invalid_data)
        self.assertEqual(form.is_valid(), False)
        error_message = form.errors['arxiv_identifier'][0]
        self.assertRegex(error_message, re.compile('already exists'))

    def test_commentary_without_arxiv_identifier_is_invalid(self):
        invalid_data = {**self.valid_form_data, **{'arxiv_identifier': ''}}
        form = RequestArxivPreprintForm(invalid_data)
        self.assertEqual(form.is_valid(), False)
