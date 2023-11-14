__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase

from ..factories import JobApplicationFactory, JobOpeningFactory


class TestJobOpeningFactory(TestCase):
    def test_can_create_job_openings(self):
        job_opening = JobOpeningFactory()
        self.assertIsNotNone(job_opening)


class TestJobApplicationFactory(TestCase):
    def test_can_create_job_applications(self):
        job_application = JobApplicationFactory()
        self.assertIsNotNone(job_application)
