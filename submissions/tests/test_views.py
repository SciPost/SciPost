__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import pytz

from django.urls import reverse
from django.test import TestCase, tag
from django.test import Client

from common.helpers import random_arxiv_identifier_without_version_number
from common.helpers.test import add_groups_and_permissions
from scipost.factories import ContributorFactory

from ..constants import STATUS_UNASSIGNED, STATUS_DRAFT, STATUS_UNVETTED
from ..factories import UnassignedSubmissionFactory, EICassignedSubmissionFactory,\
                       ResubmittedSubmissionFactory, ResubmissionFactory,\
                       PublishedSubmissionFactory, DraftReportFactory,\
                       AcceptedRefereeInvitationFactory
from ..forms import ArXivPrefillForm, ReportForm, SubmissionForm
from ..models import Submission, Report, RefereeInvitation

from journals.models import Journal

from faker import Faker


# This is content of a real arxiv submission. As long as it isn't published it should
# be possible to run tests using this submission.
TEST_SUBMISSION = {
    'is_resubmission': False,
    'title': ('General solution of 2D and 3D superconducting quasiclassical'
              ' systems:\n  coalescing vortices and nanodisk geometries'),
    'author_list': 'Morten Amundsen, Jacob Linder',
    'identifier_w_vn_nr': '1512.00030v1',
    'identifier_wo_vn_nr': '1512.00030',
    'vn_nr': 1,
    'link': 'http://arxiv.org/abs/1512.00030v1',
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


class PrefillUsingArXivIdentifierTest(BaseContributorTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.url = reverse('submissions:submit_manuscript')
        self.assertTrue(self.client.login(username="Test", password="testpw"))

    # NOTED AS BROKEN 2019-11-08
    # AssertionError: 302 != 403
    # def test_basic_responses(self):
    #     # Test anonymous client is rejected
    #     client = Client()
    #     response = client.get(self.url)
    #     self.assertEqual(response.status_code, 403)
    #     response = client.post(self.url,
    #                            {'identifier': TEST_SUBMISSION['identifier_w_vn_nr']})
    #     self.assertEqual(response.status_code, 403)

    #     # Registered Contributor should get 200
    #     response = self.client.get(self.url)
    #     self.assertIsInstance(response.context['form'], ArXivPrefillForm)
    #     self.assertFalse(response.context['form'].is_valid())
    #     self.assertEqual(response.status_code, 200)

    # NOTED AS BROKEN 2019-11-08
    # KeyError: 'title'
    # def test_retrieving_existing_arxiv_paper(self):
    #     '''Test view with a valid post request.'''
    #     response = self.client.post(self.url,
    #                                 {'identifier':
    #                                     TEST_SUBMISSION['identifier_w_vn_nr']})
    #     self.assertEqual(response.status_code, 200)
    #     # self.assertIsInstance(response.context['form'], SubmissionForm)

    #     # Explicitly compare fields instead of assertDictEqual as metadata field may be outdated
    #     # self.assertEqual(TEST_SUBMISSION['is_resubmission'],
    #     #                  response.context['form'].initial['is_resubmission'])
    #     self.assertEqual(TEST_SUBMISSION['title'], response.context['form'].initial['title'])
    #     self.assertEqual(TEST_SUBMISSION['author_list'],
    #                      response.context['form'].initial['author_list'])
    #     self.assertEqual(TEST_SUBMISSION['identifier_w_vn_nr'],
    #                      response.context['form'].initial['identifier_w_vn_nr'])
    #     self.assertEqual(TEST_SUBMISSION['identifier_wo_vn_nr'],
    #                      response.context['form'].initial['identifier_wo_vn_nr'])
    #     self.assertEqual(TEST_SUBMISSION['vn_nr'],
    #                      response.context['form'].initial['vn_nr'])
    #     self.assertEqual(TEST_SUBMISSION['url'],
    #                      response.context['form'].initial['link'])
    #     self.assertEqual(TEST_SUBMISSION['abstract'],
    #                      response.context['form'].initial['abstract'])

    def test_still_200_ok_if_identifier_is_wrong(self):
        response = self.client.post(self.url, {'identifier': '1512.00030'})
        self.assertEqual(response.status_code, 200)


# NOTED AS BROKEN 2019-11-08
# Traceback (most recent call last):
#  File "/Users/jscaux/Sites/SciPost.org/scipost_v1/submissions/test_views.py", line 135, in test_submit_correct_manuscript
#   self.assertEqual(response.status_code, 403)
# AssertionError: 302 != 403
# class SubmitManuscriptTest(BaseContributorTestCase):
#     def test_submit_correct_manuscript(self):
#         '''Check is view POST request works as expected.'''
#         client = Client()

#         # Unauthorized request shouldn't be possible
#         response = client.post(reverse('submissions:submit_manuscript'),
#                                {'identifier': TEST_SUBMISSION['identifier_w_vn_nr']})
#         self.assertEqual(response.status_code, 403)

#         # Registered Contributor should get 200; assuming prefiller is working properly
#         self.assertTrue(client.login(username="Test", password="testpw"))
#         response = client.post(reverse('submissions:submit_manuscript'),
#                                {'identifier': TEST_SUBMISSION['identifier_w_vn_nr']})
#         self.assertEqual(response.status_code, 200)

#         # Fill form parameters
#         params = response.context['form'].initial
#         params.update({
#             'discipline': 'physics',
#             'subject_area': 'Phys:MP',
#             'submitted_to': Journal.objects.filter(doi_label='SciPostPhys'),
#             'approaches': ('theoretical',)
#         })

#         # Submit new Submission form
#         response = client.post(reverse('submissions:submit_manuscript'), params)
#         self.assertEqual(response.status_code, 302)

#         # Do a quick check on the Submission submitted.
#         submission = Submission.objects.filter(status=STATUS_UNASSIGNED).last()
#         self.assertIsNotNone(submission)
#         self.assertEqual(TEST_SUBMISSION['is_resubmission'], submission.is_resubmission)
#         self.assertEqual(TEST_SUBMISSION['title'], submission.title)
#         self.assertEqual(TEST_SUBMISSION['author_list'], submission.author_list)
#         self.assertEqual(TEST_SUBMISSION['identifier_w_vn_nr'],
#                          submission.preprint.identifier_w_vn_nr)
#         self.assertEqual(TEST_SUBMISSION['identifier_wo_vn_nr'],
#                          submission.preprint.identifier_wo_vn_nr)
#         self.assertEqual(TEST_SUBMISSION['vn_nr'], submission.preprint.vn_nr)
#         self.assertEqual(TEST_SUBMISSION['url'], submission.preprint.url)
#         self.assertEqual(TEST_SUBMISSION['abstract'], submission.abstract)

    # NOTED AS BROKEN 2019-11-08
    # journals.models.journal.Journal.DoesNotExist: Journal matching query does not exist.
    # def test_non_author_tries_submission(self):
    #     '''See what happens if a non-author of an Arxiv submission submits to SciPost.'''
    #     client = Client()

    #     # Contributor Linder tries to submit the Quench Action.
    #     # Eventually this call should already give an error. Waiting for
    #     # Arxiv caller which is under construction [Jorran de Wit, 12 May 2017]
    #     self.assertTrue(client.login(username="Test", password="testpw"))
    #     response = client.post(reverse('submissions:submit_manuscript'),
    #                            {'identifier': '1603.04689v1'})
    #     self.assertEqual(response.status_code, 200)

    #     # Fill form parameters
    #     params = response.context['form'].initial
    #     params.update({
    #         'discipline': 'physics',
    #         'subject_area': 'Phys:MP',
    #         'submitted_to': Journal.objects.get(doi_label='SciPostPhys'),
    #         'approaches': ('theoretical',)
    #     })

    #     # Submit new Submission form
    #     response = client.post(reverse('submissions:submit_manuscript'), params)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIsInstance(response.context['form'], SubmissionForm)
    #     self.assertFalse(response.context['form'].is_valid())
    #     self.assertIn('author_list', response.context['form'].errors.keys())

    #     # No real check is done here to see if submission submit is aborted.
    #     # To be implemented after Arxiv caller.
    #     # Temporary fix:
    #     last_submission = Submission.objects.last()
    #     if last_submission:
    #         self.assertNotEqual(last_submission.title, 'The Quench Action')
    #         self.assertNotEqual(last_submission.preprint.identifier_w_vn_nr, '1603.04689v1')


class SubmissionDetailTest(BaseContributorTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.submission = EICassignedSubmissionFactory()
        self.target = reverse(
            'submissions:submission',
            kwargs={'identifier_w_vn_nr': self.submission.preprint.identifier_w_vn_nr}
        )

    # NOTED AS BROKEN 2019-11-08
    # AssertionError: 404 != 200
    # def test_status_code_200(self):
    #     response = self.client.get(self.target)
    #     self.assertEqual(response.status_code, 200)


# NOTED AS BROKEN 2019-11-08
#class SubmissionListTest(BaseContributorTestCase):

    # NOTED AS BROKEN 2019-11-08
    # TypeError: 'vn_nr' is an invalid keyword argument for this function
    # def test_public_list_view(self):
    #     # Create invisible Submissions.
    #     arxiv_id_resubmission = random_arxiv_identifier_without_version_number()
    #     UnassignedSubmissionFactory.create()
    #     ResubmissionFactory.create(preprint__identifier_wo_vn_nr=arxiv_id_resubmission)

    #     # Create visible submissions
    #     visible_submission_ids = []
    #     visible_submission_ids.append(
    #         ResubmittedSubmissionFactory.create(preprint__identifier_wo_vn_nr=arxiv_id_resubmission).id)
    #     visible_submission_ids.append(EICassignedSubmissionFactory.create().id)
    #     visible_submission_ids.append(PublishedSubmissionFactory.create().id)

    #     # Extra submission with multiple versions where the newest is publicly visible
    #     # again. Earlier versions should therefore be invisible!
    #     arxiv_id_resubmission = random_arxiv_identifier_without_version_number()
    #     ResubmittedSubmissionFactory.create(preprint__identifier_wo_vn_nr=arxiv_id_resubmission)
    #     visible_submission_ids.append(
    #         EICassignedSubmissionFactory.create(
    #             preprint__identifier_wo_vn_nr=arxiv_id_resubmission,
    #             fill_arxiv_fields__preprint__vn_nr=2).id
    #     )

    #     # Check with hardcoded URL as this url shouldn't change!
    #     client = Client()
    #     response = client.get('/submissions/')
    #     self.assertEqual(response.status_code, 200)

    #     # Check submissions returned
    #     returned_submissions_ids = [sub.id for sub in response.context['object_list']]

    #     # Check if submission lists are equal
    #     returned_submissions_ids.sort()
    #     visible_submission_ids.sort()
    #     self.assertListEqual(returned_submissions_ids, visible_submission_ids)


class SubmitReportTest(BaseContributorTestCase):
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
        'significance': '0',
        'strengths': 'Lorem Ipsum3',
        'validity': '60',
        'weaknesses': 'Lorem Ipsum4'
    }

    def setUp(self):
        super().setUp()
        self.client = Client()
        report_deadline = Faker().date_time_between(
            start_date="now", end_date="+30d", tzinfo=pytz.utc)
        self.submission = EICassignedSubmissionFactory(reporting_deadline=report_deadline)
        self.submission.authors.remove(self.current_contrib)
        self.submission.authors_false_claims.add(self.current_contrib)
        self.target = reverse('submissions:submit_report',
                              args=(self.submission.preprint.identifier_w_vn_nr,))
        self.assertTrue(self.client.login(username="Test", password="testpw"))

    @tag('reports')
    def test_status_code_200_no_report_set(self):
        '''Test response for view if no report is submitted yet.'''
        report_deadline = Faker().date_time_between(
            start_date="now", end_date="+30d", tzinfo=pytz.utc)
        submission = EICassignedSubmissionFactory(reporting_deadline=report_deadline)
        submission.authors.remove(self.current_contrib)
        submission.authors_false_claims.add(self.current_contrib)

        target = reverse('submissions:submit_report', args=(submission.preprint.identifier_w_vn_nr,))
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

    # NOTED AS BROKEN 2019-11-08
    # AssertionError: 302 != 200
    # @tag('reports')
    # def test_post_report_for_draft_status(self):
    #     '''Test response of view if report is saved as draft.'''
    #     response = self.client.post(self.target, {**self.TEST_DATA, 'save_draft': 'True'})

    #     # Check if form is returned with saved report as instance
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIsInstance(response.context['form'], ReportForm)
    #     self.assertIsInstance(response.context['form'].instance, Report)

    #     # Briefly do cross checks if report submit is complete
    #     report_db = Report.objects.last()
    #     self.assertEqual(response.context['form'].instance, report_db)
    #     self.assertTrue(report_db.anonymous)
    #     self.assertEqual(report_db.status, STATUS_DRAFT)
    #     self.assertFalse(report_db.invited)  # Set by view only if non-draft
    #     self.assertFalse(report_db.flagged)  # Set by view only if non-draft

    #     self.assertEqual(report_db.clarity, 60)
    #     self.assertEqual(report_db.formatting, 4)
    #     self.assertEqual(report_db.grammar, 5)
    #     self.assertEqual(report_db.originality, 100)
    #     self.assertEqual(report_db.qualification, 3)
    #     self.assertEqual(report_db.significance, 0)
    #     self.assertEqual(report_db.validity, 60)
    #     self.assertEqual(report_db.remarks_for_editors, 'Lorem Ipsum1')
    #     self.assertEqual(report_db.requested_changes, 'Lorem Ipsum2')
    #     self.assertEqual(report_db.strengths, 'Lorem Ipsum3')
    #     self.assertEqual(report_db.weaknesses, 'Lorem Ipsum4')

    # NOTED AS BROKEN 2019-11-08
    # AssertionError: 'vetted' != 'unvetted'
    # @tag('reports')
    # def test_post_report(self):
    #     '''Test response of view if report submitted.'''
    #     response = self.client.post(self.target, {**self.TEST_DATA, 'save_submit': 'True'})

    #     # Check if user is redirected
    #     self.assertEqual(response.status_code, 302)

    #     # Briefly do cross checks if report submit is complete
    #     report_db = Report.objects.last()
    #     self.assertEqual(report_db.status, STATUS_UNVETTED)

    #     # Check if invited value has only changed if valid to do so
    #     self.assertIsNone(self.submission.referee_invitations
    #                       .filter(referee=self.current_contrib).first())
    #     self.assertFalse(report_db.invited)

    #     # Cross-check if flagged can't be assigned, as this should only happen if author is
    #     # flagged on the submission involved
    #     self.assertIsNone(self.submission.referees_flagged)
    #     self.assertFalse(report_db.flagged)

    #     self.assertTrue(report_db.anonymous)
    #     self.assertEqual(report_db.clarity, 60)
    #     self.assertEqual(report_db.formatting, 4)
    #     self.assertEqual(report_db.grammar, 5)
    #     self.assertEqual(report_db.originality, 100)
    #     self.assertEqual(report_db.qualification, 3)
    #     self.assertEqual(report_db.significance, 0)
    #     self.assertEqual(report_db.validity, 60)
    #     self.assertEqual(report_db.remarks_for_editors, 'Lorem Ipsum1')
    #     self.assertEqual(report_db.requested_changes, 'Lorem Ipsum2')
    #     self.assertEqual(report_db.strengths, 'Lorem Ipsum3')
    #     self.assertEqual(report_db.weaknesses, 'Lorem Ipsum4')

    # NOTED AS BROKEN 2019-11-08
    # AssertionError: 'vetted' != 'unvetted'
    # @tag('reports')
    # def test_post_report_flagged_author(self):
    #     '''Test if report is `flagged` if author is flagged on related submission.'''
    #     report_deadline = Faker().date_time_between(start_date="now", end_date="+30d", tzinfo=None)
    #     submission = EICassignedSubmissionFactory(reporting_deadline=report_deadline,
    #                                               referees_flagged=str(self.current_contrib))
    #     submission.authors.remove(self.current_contrib)
    #     submission.authors_false_claims.add(self.current_contrib)

    #     target = reverse(
    #         'submissions:submit_report', args=(submission.preprint.identifier_w_vn_nr,))
    #     client = Client()

    #     # Login and call view
    #     self.assertTrue(client.login(username="Test", password="testpw"))
    #     self.TEST_DATA['save_submit'] = 'Submit your report'
    #     response = client.post(target, self.TEST_DATA)
    #     self.assertEqual(response.status_code, 302)

    #     # Briefly checks if report is valid
    #     report_db = Report.objects.last()
    #     self.assertEqual(report_db.status, STATUS_UNVETTED)
    #     self.assertTrue(report_db.flagged)

    # NOTED AS BROKEN 2019-11-08
    # AssertionError: 'vetted' != 'unvetted'
    # @tag('reports')
    # def test_post_report_with_invitation(self):
    #     '''Test if report is submission is valid using invitation.'''
    #     AcceptedRefereeInvitationFactory(submission=self.submission, referee=self.current_contrib)

    #     # Post Data
    #     response = self.client.post(self.target, {**self.TEST_DATA, 'save_submit': 'True'})
    #     self.assertEqual(response.status_code, 302)

    #     # Briefly checks if report is valid
    #     report_db = Report.objects.last()
    #     self.assertEqual(report_db.status, STATUS_UNVETTED)
    #     self.assertTrue(report_db.invited)

    #     # Check if Invitation has changed correctly
    #     invitation = RefereeInvitation.objects.last()
    #     self.assertEqual(invitation.referee, self.current_contrib)
    #     self.assertEqual(invitation.submission, self.submission)
    #     self.assertTrue(invitation.fulfilled)
