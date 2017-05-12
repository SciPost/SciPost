import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test import Client

from common.helpers.test import add_groups_and_permissions
from scipost.factories import ContributorFactory
# from scipost.models import Contributor

from .constants import STATUS_UNASSIGNED
from .factories import EICassignedSubmissionFactory
from .forms import SubmissionForm, SubmissionIdentifierForm
from .models import Submission

# This is content of a real arxiv submission. As long as it isn't published it should
# be possible to run tests using this submission.
TEST_SUBMISSION = {
    'is_resubmission': False,
    'title': ('General solution of 2D and 3D superconducting quasiclassical'
              ' systems:\n  coalescing vortices and nanodisk geometries'),
    'author_list': 'Morten Amundsen, Jacob Linder',
    'arxiv_identifier_w_vn_nr': '1512.00030v1',
    'arxiv_identifier_wo_vn_nr': '1512.00030',
    'arxiv_vn_nr': 1,
    'arxiv_link': 'http://arxiv.org/abs/1512.00030v1',
    'abstract': ('In quasiclassical Keldysh theory, the Green function matrix $\\check{g}$'
                 ' is\nused to compute a variety of physical quantities in mesoscopic syst'
                 'ems.\nHowever, solving the set of non-linear differential equations that'
                 ' provide\n$\\check{g}$ becomes a challenging task when going to higher s'
                 'patial dimensions\nthan one. Such an extension is crucial in order to de'
                 'scribe physical phenomena\nlike charge/spin Hall effects and topological'
                 ' excitations like vortices and\nskyrmions, none of which can be captured'
                 ' in one-dimensional models. We here\npresent a numerical finite element '
                 'method which solves the 2D and 3D\nquasiclassical Usadel equation, witho'
                 'ut any linearisation, relevant for the\ndiffusive regime. We show the ap'
                 'plication of this on two model systems with\nnon-trivial geometries: (i)'
                 ' a bottlenecked Josephson junction with external\nflux and (ii) a nanodi'
                 'sk ferromagnet deposited on top of a superconductor. We\ndemonstrate tha'
                 't it is possible to control externally not only the geometrical\narray i'
                 'n which superconducting vortices arrange themselves, but also to cause\n'
                 'coalescence and thus tune the number of vortices. The finite element met'
                 'hod\npresented herein could pave the way for gaining insight in physical'
                 ' phenomena\nwhich so far have remained largely unexplored due to the com'
                 'plexity of solving\nthe full quasiclassical equations in higher dimensio'
                 'ns.')
}


class BaseContributorTestCase(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        ContributorFactory.create_batch(5)
        ContributorFactory.create(
            user__last_name='Linder',  # To pass the author check in create submissions view
            user__username='Test',
            user__password='testpw'
        )


class PrefillUsingIdentifierTest(BaseContributorTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.url = reverse('submissions:prefill_using_identifier')
        self.assertTrue(self.client.login(username="Test", password="testpw"))

    def test_basic_responses(self):
        # Test anonymous client is rejected
        client = Client()
        response = client.get(self.url)
        self.assertEqual(response.status_code, 403)
        response = client.post(self.url,
                               {'identifier': TEST_SUBMISSION['arxiv_identifier_w_vn_nr']})
        self.assertEqual(response.status_code, 403)

        # Registered Contributor should get 200
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_retrieving_existing_arxiv_paper(self):
        '''Test view with a valid post request.'''
        response = self.client.post(self.url,
                                    {'identifier':
                                        TEST_SUBMISSION['arxiv_identifier_w_vn_nr']})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], SubmissionForm)
        self.assertIsInstance(response.context['identifierform'], SubmissionIdentifierForm)
        self.assertTrue(response.context['identifierform'].is_valid())

        # Explicitly compare fields instead of assertDictEqual as metadata field may be outdated
        self.assertEqual(TEST_SUBMISSION['is_resubmission'],
                         response.context['form'].initial['is_resubmission'])
        self.assertEqual(TEST_SUBMISSION['title'], response.context['form'].initial['title'])
        self.assertEqual(TEST_SUBMISSION['author_list'],
                         response.context['form'].initial['author_list'])
        self.assertEqual(TEST_SUBMISSION['arxiv_identifier_w_vn_nr'],
                         response.context['form'].initial['arxiv_identifier_w_vn_nr'])
        self.assertEqual(TEST_SUBMISSION['arxiv_identifier_wo_vn_nr'],
                         response.context['form'].initial['arxiv_identifier_wo_vn_nr'])
        self.assertEqual(TEST_SUBMISSION['arxiv_vn_nr'],
                         response.context['form'].initial['arxiv_vn_nr'])
        self.assertEqual(TEST_SUBMISSION['arxiv_link'],
                         response.context['form'].initial['arxiv_link'])
        self.assertEqual(TEST_SUBMISSION['abstract'],
                         response.context['form'].initial['abstract'])

    def test_still_200_ok_if_identifier_is_wrong(self):
        response = self.client.post(self.url, {'identifier': '1512.00030'})
        self.assertEqual(response.status_code, 200)


class SubmitManuscriptTest(BaseContributorTestCase):
    def test_submit_correct_manuscript(self):
        '''Check is view POST request works as expected.'''
        client = Client()

        # Unauthorized request shouldn't be possible
        response = client.post(reverse('submissions:prefill_using_identifier'),
                               {'identifier': TEST_SUBMISSION['arxiv_identifier_w_vn_nr']})
        self.assertEquals(response.status_code, 403)

        # Registered Contributor should get 200; assuming prefiller is working properly
        self.assertTrue(client.login(username="Test", password="testpw"))
        response = client.post(reverse('submissions:prefill_using_identifier'),
                               {'identifier': TEST_SUBMISSION['arxiv_identifier_w_vn_nr']})
        self.assertEqual(response.status_code, 200)

        # Fill form parameters
        params = response.context['form'].initial
        params.update({
            'discipline': 'physics',
            'subject_area': 'Phys:MP',
            'submitted_to_journal': 'SciPostPhys',
            'submission_type': 'Article',
            'domain': 'T'
        })
        params['metadata'] = json.dumps(params['metadata'], separators=(',', ':'))

        # Submit new Submission form
        response = client.post(reverse('submissions:submit_manuscript'), params)
        self.assertEqual(response.status_code, 302)

        # Do a quick check on the Submission submitted.
        submission = Submission.objects.filter(status=STATUS_UNASSIGNED).last()
        self.assertIsNotNone(submission)
        self.assertEqual(TEST_SUBMISSION['is_resubmission'], submission.is_resubmission)
        self.assertEqual(TEST_SUBMISSION['title'], submission.title)
        self.assertEqual(TEST_SUBMISSION['author_list'], submission.author_list)
        self.assertEqual(TEST_SUBMISSION['arxiv_identifier_w_vn_nr'],
                         submission.arxiv_identifier_w_vn_nr)
        self.assertEqual(TEST_SUBMISSION['arxiv_identifier_wo_vn_nr'],
                         submission.arxiv_identifier_wo_vn_nr)
        self.assertEqual(TEST_SUBMISSION['arxiv_vn_nr'], submission.arxiv_vn_nr)
        self.assertEqual(TEST_SUBMISSION['arxiv_link'], submission.arxiv_link)
        self.assertEqual(TEST_SUBMISSION['abstract'], submission.abstract)

    def test_non_author_tries_submission(self):
        '''See what happens if a non-author of an Arxiv submission submits to SciPost.'''
        client = Client()

        # Contributor Linder tries to submit the Quench Action.
        # Eventually this call should already give an error. Waiting for
        # Arxiv caller which is under construction [Jorran de Wit, 12 May 2017]
        self.assertTrue(client.login(username="Test", password="testpw"))
        response = client.post(reverse('submissions:prefill_using_identifier'),
                               {'identifier': '1603.04689v1'})
        self.assertEqual(response.status_code, 200)

        # Fill form parameters
        params = response.context['form'].initial
        params.update({
            'discipline': 'physics',
            'subject_area': 'Phys:MP',
            'submitted_to_journal': 'SciPostPhys',
            'submission_type': 'Article',
            'domain': 'T'
        })
        params['metadata'] = json.dumps(params['metadata'], separators=(',', ':'))

        # Submit new Submission form
        response = client.post(reverse('submissions:submit_manuscript'), params)
        self.assertEqual(response.status_code, 302)

        # No real check is done here to see if submission submit is aborted.
        # To be implemented after Arxiv caller.
        # Temporary fix:
        last_submission = Submission.objects.last()
        if last_submission:
            self.assertNotEqual(last_submission.title, 'The Quench Action')
            self.assertNotEqual(last_submission.arxiv_identifier_w_vn_nr, '1603.04689v1')


class SubmissionDetailTest(BaseContributorTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.submission = EICassignedSubmissionFactory()
        self.target = reverse(
            'submissions:submission',
            kwargs={'arxiv_identifier_w_vn_nr': self.submission.arxiv_identifier_w_vn_nr}
        )

    def test_status_code_200(self):
        response = self.client.get(self.target)
        self.assertEqual(response.status_code, 200)
