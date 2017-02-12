from django.test import TestCase

from .services import ArxivCaller

from submissions.models import Submission


class ArxivCallerTest(TestCase):

    def test_correct_lookup(self):
        caller = ArxivCaller(Submission, '1611.09574v1')

        caller.process()

        self.assertEqual(caller.is_valid(), True)
        self.assertIn('entries', caller.metadata)

    def test_errorcode_for_non_existing_paper(self):
        caller = ArxivCaller(Submission, '2611.09574v1')

        caller.process()
        self.assertEqual(caller.is_valid(), False)
        self.assertEqual(caller.errorcode, 'preprint_does_not_exist')

    def test_errorcode_for_bad_request(self):
        caller = ArxivCaller(Submission, '161109574v1')

        caller.process()
        self.assertEqual(caller.is_valid(), False)
        self.assertEqual(caller.errorcode, 'arxiv_bad_request')

    def test_errorcode_for_already_published_journal_ref(self):
        caller = ArxivCaller(Submission, '1412.0006v1')

        caller.process()
        self.assertEqual(caller.is_valid(), False)
        self.assertEqual(caller.errorcode, 'paper_published_journal_ref')
        self.assertNotEqual(caller.arxiv_journal_ref, '')

    def test_errorcode_no_version_nr(self):
        # Should be already caught in form validation
        caller = ArxivCaller(Submission, '1412.0006')

        caller.process()
        self.assertEqual(caller.is_valid(), False)
        self.assertEqual(caller.errorcode, 'bad_identifier')
