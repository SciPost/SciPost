__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import datetime

from django.conf import settings
from django.test import TestCase
from django.utils.timezone import make_aware
from journals.factories import JournalFactory
from proceedings.factories import ProceedingsFactory

from production.factories import ProofsRepositoryFactory
from production.models import ProofsRepository
from profiles.factories import ProfileFactory
from submissions.constants import EIC_REC_PUBLISH
from submissions.factories.decision import EditorialDecisionFactory
from submissions.factories.submission import SubmissionFactory


class TestProofRepository(TestCase):
    def test_repo_name_existing_profile(self):
        proofs_repo = ProofsRepositoryFactory(
            stream__submission__preprint__identifier_w_vn_nr="scipost_202101_00001v1",
        )

        proofs_repo.stream.submission.author_list = "John F. Doe"
        proofs_repo.stream.submission.save()

        ProfileFactory(first_name="John Frank", last_name="Doe")

        self.assertEqual(
            ProofsRepository._get_repo_name(proofs_repo.stream),
            "scipost_202101_00001v1_Doe",
        )

    def test_repo_name_nonexisting_profile(self):
        proofs_repo = ProofsRepositoryFactory(
            stream__submission__preprint__identifier_w_vn_nr="scipost_202101_00001v1"
        )

        proofs_repo.stream.submission.author_list = "Kim J. Ranger"
        proofs_repo.stream.submission.save()

        self.assertEqual(
            ProofsRepository._get_repo_name(proofs_repo.stream),
            "scipost_202101_00001v1_Ranger",
        )

    def test_repo_name_double_last_name_profile(self):
        proofs_repo = ProofsRepositoryFactory(
            stream__submission__preprint__identifier_w_vn_nr="scipost_202302_00525v1"
        )

        proofs_repo.stream.submission.author_list = "Liam Magnus Carter"
        proofs_repo.stream.submission.save()

        ProfileFactory(first_name="Liam", last_name="Magnus Carter")

        self.assertEqual(
            ProofsRepository._get_repo_name(proofs_repo.stream),
            "scipost_202302_00525v1_Magnus-Carter",
        )

    def test_repo_name_two_authors(self):
        proofs_repo = ProofsRepositoryFactory(
            stream__submission__preprint__identifier_w_vn_nr="1234.56789v1"
        )

        proofs_repo.stream.submission.author_list = "Xi Yang and Zhu Lee"

        self.assertEqual(
            ProofsRepository._get_repo_name(proofs_repo.stream),
            "1234.56789v1_Yang",
        )

    def test_repo_name_accented_authors(self):
        ProfileFactory(first_name="Ella", last_name="Vérsøüsær")
        proofs_repo = ProofsRepositoryFactory(
            stream__submission__preprint__identifier_w_vn_nr="5212.24912v4",
            stream__submission__author_list="Ella Vérsøüsær",
        )

        self.assertEqual(
            ProofsRepository._get_repo_name(proofs_repo.stream),
            "5212.24912v4_Versousaer",
        )

    def test_repo_paths_scipostphys(self):
        settings.GITLAB_ROOT = "ProjectRoot"

        ProfileFactory(first_name="Ryan", last_name="MacVigor")

        submission = SubmissionFactory(
            preprint__identifier_w_vn_nr="scipost_199402_00223v3",
            author_list="Ryan MacVigor",
        )

        EditorialDecisionFactory(
            submission=submission,
            for_journal=JournalFactory.SciPostPhysics(),
            taken_on=make_aware(datetime.datetime(1994, 2, 20)),
            decision=EIC_REC_PUBLISH,
        )

        proofs_repo = ProofsRepositoryFactory(
            stream__submission=submission,
            stream__opened=make_aware(datetime.datetime(1994, 2, 23)),
        )

        self.assertEqual(
            proofs_repo.git_path,
            "ProjectRoot/Proofs/SciPostPhys/1994/02/scipost_199402_00223v3_MacVigor",
        )

        self.assertIn(
            "ProjectRoot/Templates/SciPostPhys",
            proofs_repo.template_paths,
        )

    def test_repo_paths_scipostphysproc(self):
        settings.GITLAB_ROOT = "ProjectRoot"

        scipost_phys_proc = JournalFactory.SciPostPhysicsProc()

        topology_conf = ProceedingsFactory(
            event_end_date=datetime.datetime(2019, 5, 5),
            event_start_date=datetime.datetime(2019, 5, 20),
            event_suffix="TopCon2019",
        )

        ProfileFactory(first_name="Tylla M.", last_name="Jones")

        submission = SubmissionFactory(
            preprint__identifier_w_vn_nr="scipost_200101_00323v2",
            author_list="Tylla Maria Jones",
            proceedings=topology_conf,
        )

        EditorialDecisionFactory(
            submission=submission,
            for_journal=scipost_phys_proc,
            decision=EIC_REC_PUBLISH,
        )

        proofs_repo = ProofsRepositoryFactory(
            stream__submission=submission,
        )

        self.assertEqual(
            proofs_repo.git_path,
            "ProjectRoot/Proofs/SciPostPhysProc/2019/TopCon2019/scipost_200101_00323v2_Jones",
        )

        self.assertIn(
            "ProjectRoot/Templates/SciPostPhysProc/2019/TopCon2019",
            proofs_repo.template_paths,
        )
