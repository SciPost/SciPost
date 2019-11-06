__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.test import TestCase

from .services import ArxivCaller, DOICaller

from submissions.models import Submission


class ArxivCallerTest(TestCase):
    def test_identifier_new_style(self):
        caller = ArxivCaller('1612.07611v1')
        self.assertTrue(caller.is_valid)
        correct_data = {
            'arxiv_link': 'https://arxiv.org/abs/1612.07611v1', 'author_list': 'Roman Krčmár, Andrej Gendiar, Tomotoshi Nishino', 'abstract': 'The Berezinskii-Kosterlitz-Thouless (BKT) transitions of the six-state clock\nmodel on the square lattice are investigated by means of the corner-transfer\nmatrix renormalization group method. The classical analogue of the entanglement\nentropy $S( L, T )$ is calculated for $L$ by $L$ square system up to $L = 129$,\nas a function of temperature $T$. The entropy has a peak at $T = T^{*}_{~}( L\n)$, where the temperature depends on both $L$ and boundary conditions. Applying\nthe finite-size scaling to $T^{*}_{~}( L )$ and assuming the presence of BKT\ntransitions, the transition temperature is estimated to be $T_1^{~} = 0.70$ and\n$T_2^{~} = 0.88$. The obtained results agree with previous analyses. It should\nbe noted that no thermodynamic function is used in this study.', 'pub_abstract': 'The Berezinskii-Kosterlitz-Thouless (BKT) transitions of the six-state clock\nmodel on the square lattice are investigated by means of the corner-transfer\nmatrix renormalization group method. The classical analogue of the entanglement\nentropy $S( L, T )$ is calculated for $L$ by $L$ square system up to $L = 129$,\nas a function of temperature $T$. The entropy has a peak at $T = T^{*}_{~}( L\n)$, where the temperature depends on both $L$ and boundary conditions. Applying\nthe finite-size scaling to $T^{*}_{~}( L )$ and assuming the presence of BKT\ntransitions, the transition temperature is estimated to be $T_1^{~} = 0.70$ and\n$T_2^{~} = 0.88$. The obtained results agree with previous analyses. It should\nbe noted that no thermodynamic function is used in this study.', 'title': 'Phase transition of the six-state clock model observed from the\n  entanglement entropy', 'pub_date': datetime.date(2016, 12, 22)
        }
        self.assertDictEqual(caller.data, correct_data)

    def test_identifier_old_style(self):
        caller = ArxivCaller('cond-mat/0612480')
        self.assertTrue(caller.is_valid)
        correct_data = {'arxiv_link': 'https://arxiv.org/abs/cond-mat/0612480v2', 'pub_date': datetime.date(2006, 12, 19), 'author_list': 'Kouji Ueda, Chenglong Jin, Naokazu Shibata, Yasuhiro Hieida, Tomotoshi Nishino', 'abstract': 'A kind of least action principle is introduced for the discrete time\nevolution of one-dimensional quantum lattice models. Based on this principle,\nwe obtain an optimal condition for the matrix product states on succeeding time\nslices generated by the real-time density matrix renormalization group method.\nThis optimization can also be applied to classical simulations of quantum\ncircuits. We discuss the time reversal symmetry in the fully optimized MPS.', 'pub_abstract': 'A kind of least action principle is introduced for the discrete time\nevolution of one-dimensional quantum lattice models. Based on this principle,\nwe obtain an optimal condition for the matrix product states on succeeding time\nslices generated by the real-time density matrix renormalization group method.\nThis optimization can also be applied to classical simulations of quantum\ncircuits. We discuss the time reversal symmetry in the fully optimized MPS.', 'title': 'Least Action Principle for the Real-Time Density Matrix Renormalization\n  Group'}
        self.assertDictEqual(caller.data, correct_data)

    def valid_but_nonexistent_identifier(self):
        caller = ArxivCaller('1613.07611v1')
        self.assertEqual(caller.is_valid, False)


class DOICallerTest(TestCase):
    def test_works_for_physrev_doi(self):
        caller = DOICaller('10.1103/PhysRevB.92.214427')
        correct_data = {'title': 'Quasi-soliton scattering in quantum spin chains', 'pages': '214427', 'author_list': 'R. Vlijm, M. Ganahl, D. Fioretto, M. Brockmann, M. Haque, H. G. Evertz, J.-S. Caux', 'pub_date': '2015-12-18', 'volume': '92', 'journal': 'Physical Review B'}
        self.assertTrue(caller.is_valid)
        self.assertDictEqual(caller.data, correct_data)

    def test_works_for_scipost_doi(self):
        caller = DOICaller('10.21468/SciPostPhys.2.2.012')
        correct_data = {'author_list': 'Yannis Brun, Jerome Dubail', 'pub_date': '2017-04-04', 'volume': '2', 'title': 'One-particle density matrix of trapped one-dimensional impenetrable bosons from conformal invariance', 'pages': '012', 'journal': 'SciPost Physics'}
        self.assertTrue(caller.is_valid)
        self.assertDictEqual(caller.data, correct_data)

    def test_valid_but_non_existent_doi(self):
        caller = DOICaller('10.21468/NonExistentJournal.2.2.012')
        self.assertEqual(caller.is_valid, False)
