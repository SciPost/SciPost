from django.core.urlresolvers import reverse
from django.test import TestCase, tag
from django.test import Client

from common.helpers import random_arxiv_identifier_without_version_number
from common.helpers.test import add_groups_and_permissions
from scipost.factories import ContributorFactory

from .constants import STATUS_UNASSIGNED, STATUS_DRAFT, STATUS_UNVETTED
from .factories import UnassignedSubmissionFactory, EICassignedSubmissionFactory,\
                       ResubmittedSubmissionFactory, ResubmissionFactory,\
                       PublishedSubmissionFactory, DraftReportFactory
from .forms import RequestSubmissionForm, SubmissionIdentifierForm, ReportForm
from .models import Submission, Report

from faker import Faker


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
        self.current_contrib = ContributorFactory.create(
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
        self.assertIsInstance(response.context['form'], SubmissionIdentifierForm)
        self.assertFalse(response.context['form'].is_valid())
        self.assertEqual(response.status_code, 200)

    def test_retrieving_existing_arxiv_paper(self):
        '''Test view with a valid post request.'''
        response = self.client.post(self.url,
                                    {'identifier':
                                        TEST_SUBMISSION['arxiv_identifier_w_vn_nr']})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], RequestSubmissionForm)

        # Explicitly compare fields instead of assertDictEqual as metadata field may be outdated
        # self.assertEqual(TEST_SUBMISSION['is_resubmission'],
        #                  response.context['form'].initial['is_resubmission'])
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

        # Submit new Submission form
        response = client.post(reverse('submissions:submit_manuscript'), params)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], RequestSubmissionForm)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('author_list', response.context['form'].errors.keys())

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


class SubmissionListTest(BaseContributorTestCase):
    def test_public_list_view(self):
        # Create invisible Submissions.
        arxiv_id_resubmission = random_arxiv_identifier_without_version_number()
        UnassignedSubmissionFactory.create()
        ResubmissionFactory.create(arxiv_identifier_wo_vn_nr=arxiv_id_resubmission)

        # Create visible submissions
        visible_submission_ids = []
        visible_submission_ids.append(ResubmittedSubmissionFactory
                                      .create(arxiv_identifier_wo_vn_nr=arxiv_id_resubmission).id)
        visible_submission_ids.append(EICassignedSubmissionFactory.create().id)
        visible_submission_ids.append(PublishedSubmissionFactory.create().id)

        # Extra submission with multiple versions where the newest is publicly visible
        # again. Earlier versions should therefore be invisible!
        arxiv_id_resubmission = random_arxiv_identifier_without_version_number()
        ResubmittedSubmissionFactory.create(arxiv_identifier_wo_vn_nr=arxiv_id_resubmission)
        visible_submission_ids.append(
            EICassignedSubmissionFactory.create(
                arxiv_identifier_wo_vn_nr=arxiv_id_resubmission,
                fill_arxiv_fields__arxiv_vn_nr=2
            ).id
        )

        # Check with hardcoded URL as this url shouldn't change!
        client = Client()
        response = client.get('/submissions/')
        self.assertEqual(response.status_code, 200)

        # Check submissions returned
        returned_submissions_ids = [sub.id for sub in response.context['object_list']]

        # Check if submission lists are equal
        returned_submissions_ids.sort()
        visible_submission_ids.sort()
        self.assertListEqual(returned_submissions_ids, visible_submission_ids)


class SubmitReportTest(BaseContributorTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        report_deadline = Faker().date_time_between(start_date="now", end_date="+30d", tzinfo=None)
        self.submission = EICassignedSubmissionFactory(reporting_deadline=report_deadline)
        self.submission.authors.remove(self.current_contrib)
        self.submission.authors_false_claims.add(self.current_contrib)
        self.target = reverse('submissions:submit_report',
                              args=(self.submission.arxiv_identifier_w_vn_nr,))
        self.assertTrue(self.client.login(username="Test", password="testpw"))

    @tag('reports')
    def test_status_code_200_no_report_set(self):
        '''Test response for view if no report is submitted yet.'''
        report_deadline = Faker().date_time_between(start_date="now", end_date="+30d", tzinfo=None)
        submission = EICassignedSubmissionFactory(reporting_deadline=report_deadline)
        submission.authors.remove(self.current_contrib)
        submission.authors_false_claims.add(self.current_contrib)

        target = reverse('submissions:submit_report', args=(submission.arxiv_identifier_w_vn_nr,))
        client = Client()

        # Login and call view
        self.assertTrue(client.login(username="Test", password="testpw"))
        response = client.get(target)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['form'].instance.id)

    @tag('reports')
    def test_status_code_200_report_in_draft(self):
        '''Test response for view if report in draft exists.'''
        report = DraftReportFactory(submission=self.submission, author=self.current_contrib)
        response = self.client.get(self.target)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ReportForm)
        self.assertEqual(response.context['form'].instance, report)

    @tag('reports')
    def test_post_report_for_draft_status(self):
        '''Test response of view if report is saved as draft.'''
        TEST_DATA = {
            'anonymous': 'on',
            'clarity': '60',
            'formatting': '4',
            'grammar': '5',
            'originality': '100',
            'qualification': '3',
            'recommendation': '3',
            'remarks_for_editors': 'Lorem Ipsum1',
            'report': 'Lorem Ipsum',
            'requested_changes': 'Lorem Ipsum2',
            'save_draft': 'Save your report as draft',
            'significance': '0',
            'strengths': 'Lorem Ipsum3',
            'validity': '60',
            'weaknesses': 'Lorem Ipsum4'
        }
        response = self.client.post(self.target, TEST_DATA)

        # Check if form is returned with saved report as instance
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ReportForm)
        self.assertIsInstance(response.context['form'].instance, Report)

        # Briefly do cross checks if report submit is complete
        report_db = Report.objects.last()
        self.assertEqual(response.context['form'].instance, report_db)
        self.assertTrue(report_db.anonymous)
        self.assertEqual(report_db.status, STATUS_DRAFT)
        self.assertFalse(report_db.invited)  # Set by view only if non-draft
        self.assertFalse(report_db.flagged)  # Set by view only if non-draft

        self.assertEqual(report_db.clarity, 60)
        self.assertEqual(report_db.formatting, 4)
        self.assertEqual(report_db.grammar, 5)
        self.assertEqual(report_db.originality, 100)
        self.assertEqual(report_db.qualification, 3)
        self.assertEqual(report_db.significance, 0)
        self.assertEqual(report_db.validity, 60)
        self.assertEqual(report_db.remarks_for_editors, 'Lorem Ipsum1')
        self.assertEqual(report_db.requested_changes, 'Lorem Ipsum2')
        self.assertEqual(report_db.strengths, 'Lorem Ipsum3')
        self.assertEqual(report_db.weaknesses, 'Lorem Ipsum4')

    @tag('reports')
    def test_post_report(self):
        '''Test response of view if report submitted.'''
        TEST_DATA = {
            'anonymous': 'on',
            'clarity': '60',
            'formatting': '4',
            'grammar': '5',
            'originality': '100',
            'qualification': '3',
            'recommendation': '3',
            'remarks_for_editors': 'Lorem Ipsum1',
            'report': 'Lorem Ipsum',
            'requested_changes': 'Lorem Ipsum2',
            'save_submit': 'Submit your report',  # This dict-key makes the difference in the end
            'significance': '0',
            'strengths': 'Lorem Ipsum3',
            'validity': '60',
            'weaknesses': 'Lorem Ipsum4'
        }
        response = self.client.post(self.target, TEST_DATA)

        # Check if user is redirected
        self.assertEqual(response.status_code, 302)

        # Briefly do cross checks if report submit is complete
        report_db = Report.objects.last()
        self.assertEqual(report_db.status, STATUS_UNVETTED)

        # Check if invited value has only changed if valid to do so
        self.assertIsNone(self.submission.referee_invitations
                          .filter(referee=self.current_contrib).first())
        self.assertFalse(report_db.invited)

        # Cross-check if flagged can't be assigned, as this should only happen if author is
        # flagged on the submission involved
        self.assertIsNone(self.submission.referees_flagged)
        self.assertFalse(report_db.flagged)

        self.assertTrue(report_db.anonymous)
        self.assertEqual(report_db.clarity, 60)
        self.assertEqual(report_db.formatting, 4)
        self.assertEqual(report_db.grammar, 5)
        self.assertEqual(report_db.originality, 100)
        self.assertEqual(report_db.qualification, 3)
        self.assertEqual(report_db.significance, 0)
        self.assertEqual(report_db.validity, 60)
        self.assertEqual(report_db.remarks_for_editors, 'Lorem Ipsum1')
        self.assertEqual(report_db.requested_changes, 'Lorem Ipsum2')
        self.assertEqual(report_db.strengths, 'Lorem Ipsum3')
        self.assertEqual(report_db.weaknesses, 'Lorem Ipsum4')
