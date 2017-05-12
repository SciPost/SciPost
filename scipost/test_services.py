from django.test import TestCase

from .services import ArxivCaller, DOICaller

from submissions.models import Submission


class ArxivCallerTest(TestCase):
    def setUp(self):
        self.valid_arxiv_identifier = '1612.07611v1'

    def test_collects_metadata(self):
        raise NotImplementedError

class ArxivCallerTestOld(TestCase):
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


class DOICallerTest(TestCase):
    def test_works_for_physrev_doi(self):
        caller = DOICaller('10.1103/PhysRevB.92.214427')
        correct_data = {
            'pub_date': '2015-12-18',
            'journal': 'Physical Review B',
            'pages': '',
            'authorlist': [
                'R. Vlijm', 'M. Ganahl', 'D. Fioretto', 'M. Brockmann', 'M. Haque', 'H. G. Evertz', 'J.-S. Caux'],
            'volume': '92',
            'pub_title': 'Quasi-soliton scattering in quantum spin chains'
        }
        self.assertTrue(caller.is_valid)
        self.assertEqual(caller.data, correct_data)

    def test_works_for_scipost_doi(self):
        caller = DOICaller('10.21468/SciPostPhys.2.2.012')
        correct_data = {
            'pub_date': '2017-04-04',
            'journal': 'SciPost Physics',
            # Inexplicably, an extra space is added between 'inpenetrable' and 'bosons', but this is a
            # Crossref error.
            'pub_title': 'One-particle density matrix of trapped one-dimensional impenetrable  bosons from conformal invariance',
            'pages': '',
            'volume': '2',
            'authorlist': ['Yannis Brun', 'Jerome Dubail']
        }
        self.assertTrue(caller.is_valid)
        self.assertEqual(caller.data, correct_data)

    def test_valid_but_non_existent_doi(self):
        caller = DOICaller('10.21468/NonExistentJournal.2.2.012')
        self.assertEqual(caller.is_valid, False)
