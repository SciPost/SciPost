__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.core.management import call_command
from django.core.management.base import BaseCommand

from journals import factories as journal_factories
from scipost import factories
from submissions import factories as submission_factories


class Command(BaseCommand):
    help = "Fill database with random data for most important modules."

    def handle(self, *args, **kwargs):
        call_command("add_groups_and_permissions")

        # Contributors
        factories.ContributorFactory.create_batch(50)
        factories.VettingEditorFactory.create_batch(10)
        self.stdout.write(self.style.SUCCESS("Successfully created 60 Contributors."))

        # Create the Journals
        journal_factories.VolumeFactory.create_batch(4)
        journal_factories.IssueFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS("Successfully created 4 Journals."))

        # Submissions, reports and publications
        submission_factories.SubmissionFactory.create_batch(20)
        submission_factories.ScreeningSubmissionFactory.create_batch(20)
        submission_factories.InRefereeingSubmissionFactory.create_batch(20)
        submission_factories.ResubmittedSubmissionFactory.create_batch(10)
        submission_factories.ResubmissionFactory.create_batch(10)
        submission_factories.PublishedSubmissionFactory.create_batch(20)
        self.stdout.write(self.style.SUCCESS("Successfully created 100 Submissions."))
