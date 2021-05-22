__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from django.test import TestCase, RequestFactory

from ontology.models import AcademicField, Specialty
from scipost.factories import ContributorFactory
from ..factories import ThesisLinkFactory, VetThesisLinkFormFactory
from ..forms import RequestThesisLinkForm, VetThesisLinkForm
from common.helpers import model_form_data
from common.helpers.test import add_groups_and_permissions


class TestRequestThesisLink(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.contributor = ContributorFactory()
        self.user = self.contributor.user
        self.request = RequestFactory()
        self.request.user = self.user
        self.valid_form_data = model_form_data(
            ThesisLinkFactory(), RequestThesisLinkForm, form_kwargs={'request': self.request})
        self.valid_form_data['acad_field'] = AcademicField.objects.order_by('?').first().id
        self.valid_form_data['specialties'] = [s.id for s in Specialty.objects.order_by('?')[:3]]

    def test_valid_data_is_valid(self):
        form_data = self.valid_form_data
        form = RequestThesisLinkForm(self.valid_form_data, request=self.request)
        self.assertTrue(form.is_valid())

    def test_data_without_user_is_not_valid(self):
        form_data = self.valid_form_data
        request = RequestFactory()
        with self.assertRaises(AttributeError) as result:
            RequestThesisLinkForm(self.valid_form_data, request=request)
        self.assertTrue(result)

    def test_thesislink_is_requested_by_correct_contributor(self):
        form_data = self.valid_form_data
        form = RequestThesisLinkForm(form_data, request=self.request)

        # Check if the user is properly saved to the new ThesisLink as `requested_by`
        print(form.is_valid())
        print(form.errors)
        thesislink = form.save()
        self.assertEqual(thesislink.requested_by, self.contributor)
