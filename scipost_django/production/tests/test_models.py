__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import datetime

from django.test import TestCase

# Create your tests here.

from submissions.constants import EIC_REC_PUBLISH
from journals.models import Journal
from submissions.models import Submission, EditorialDecision
from production.models import ProductionStream, ProofsRepository
from preprints.models import Preprint
from ontology.models import AcademicField, Branch, Specialty
from colleges.models import College
from scipost.models import Contributor
from profiles.models import Profile


from django.contrib.auth.models import User


class TestProofRepository(TestCase):
    def _create_submitter_contributor(self):
        random_user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        user_profile = Profile.objects.create(
            title="DR",
            first_name="Test",
            last_name="User",
        )
        Contributor.objects.create(user=random_user, profile=user_profile)

    def _create_college(self):
        College.objects.create(
            name="College of Quantum Physics",
            acad_field=AcademicField.objects.get(name="Quantum Physics"),
            slug="college-of-quantum-physics",
            order=10,
        )

    def _create_journal(self):
        Journal.objects.create(
            college=College.objects.get(name="College of Quantum Physics"),
            name="SciPost Physics",
            name_abbrev="SciPost Phys.",
            doi_label="SciPostPhys",
            cf_metrics='{"":""}',
        )

    def _create_editorial_decision(self):
        EditorialDecision.objects.create(
            submission=Submission.objects.get(
                preprint__identifier_w_vn_nr="scipost_202101_00001v1"
            ),
            for_journal=Journal.objects.get(name="SciPost Physics"),
            decision=EIC_REC_PUBLISH,
            status=EditorialDecision.FIXED_AND_ACCEPTED,
        )

    def _create_specialty(self):
        Specialty.objects.create(
            acad_field=AcademicField.objects.get(name="Quantum Physics"),
            name="Quantum Information",
            slug="quantum-information",
            order=10,
        )

    def _create_academic_field(self):
        AcademicField.objects.create(
            branch=Branch.objects.get(name="Physics"),
            name="Quantum Physics",
            slug="quantum-physics",
            order=10,
        )

    def _create_branch(self):
        Branch.objects.create(
            name="Physics",
            slug="physics",
            order=10,
        )

    def _create_preprint(self):
        Preprint.objects.create(identifier_w_vn_nr="scipost_202101_00001v1")

    def _create_submission(self):
        submission = Submission.objects.create(
            preprint=Preprint.objects.get(
                identifier_w_vn_nr="scipost_202101_00001v1"
            ),
            submitted_to=Journal.objects.get(name="SciPost Physics"),
            title="Test submission",
            abstract="Test abstract",
            author_list="Test User",
            acad_field=AcademicField.objects.get(name="Quantum Physics"),
            # specialties=Specialty.objects.filter(name="Quantum Information"),
            submitted_by=Contributor.objects.get(user__username="testuser"),
        )
        submission.authors.add(
            Contributor.objects.get(user__username="testuser")
        )
        submission.save()

    def _create_production_stream(self):
        stream = ProductionStream.objects.create(
            submission=Submission.objects.get(
                preprint__identifier_w_vn_nr="scipost_202101_00001v1"
            ),
        )
        stream.opened = datetime.datetime(
            2021, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        )
        stream.save()

    def setUp(self):
        self._create_submitter_contributor()
        self._create_branch()
        self._create_academic_field()
        self._create_specialty()
        self._create_college()
        self._create_journal()
        self._create_preprint()
        self._create_submission()
        self._create_editorial_decision()
        self._create_production_stream()

    def test_repo_scipostphys_existing_profile(self):
        proofs_repo = ProofsRepository.objects.get(
            stream__submission__preprint__identifier_w_vn_nr="scipost_202101_00001v1"
        )

        self.assertEqual(
            proofs_repo.git_path,
            "Proofs/SciPostPhys/2021/01/scipost_202101_00001v1_User",
        )

        self.assertEqual(proofs_repo.template_path, "Templates/SciPostPhys")

    def test_repo_scipostphys_nonexisting_profile(self):
        proofs_repo = ProofsRepository.objects.get(
            stream__submission__preprint__identifier_w_vn_nr="scipost_202101_00001v1"
        )

        # delete profile
        Contributor.objects.get(user__username="testuser").profile.delete()

        self.assertEqual(
            proofs_repo.git_path,
            "Proofs/SciPostPhys/2021/01/scipost_202101_00001v1_User",
        )
        self.assertEqual(proofs_repo.template_path, "Templates/SciPostPhys")

    def test_repo_scipostphys_double_last_name_profile(self):
        proofs_repo = ProofsRepository.objects.get(
            stream__submission__preprint__identifier_w_vn_nr="scipost_202101_00001v1"
        )

        proofs_repo.stream.submission.author_list = "Test Usable User"

        user_profile = Contributor.objects.get(
            user__username="testuser"
        ).profile
        user_profile.last_name = "Usable User"
        user_profile.save()

        self.assertEqual(
            proofs_repo.git_path,
            "Proofs/SciPostPhys/2021/01/scipost_202101_00001v1_User",
        )

        self.assertEqual(proofs_repo.template_path, "Templates/SciPostPhys")
