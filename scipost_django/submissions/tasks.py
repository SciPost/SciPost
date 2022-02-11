__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from datetime import timedelta
from django.utils import timezone

from SciPost_v1.celery import app

from .models import Submission, EditorialAssignment, RefereeInvitation, Report


@app.task(bind=True)
def send_editorial_assignment_invitations(self):
    """Send invitation email to 'next EditorialAssignment' in queue."""
    qs = Submission.objects.unassigned().has_editor_invitations_to_be_sent().distinct()
    submission_ids = qs.values_list("id", flat=True)
    submissions_count = len(submission_ids)

    count = 0
    for submission_id in submission_ids:
        self.update_state(
            state="PROGRESS",
            meta={
                "progress": round(100 * count / submissions_count),
                "total_count": submissions_count,
            },
        )

        # Get EditorialAssignment to send or nothing.
        ed_assignment = EditorialAssignment.objects.next_invitation_to_be_sent(
            submission_id
        )
        if ed_assignment:
            if ed_assignment.send_invitation():
                count += 1
    return {"new_invites": count}


@app.task(bind=True)
def submit_submission_document_for_plagiarism(self):
    """Upload a new Submission document to iThenticate."""
    submissions_to_upload = Submission.objects.plagiarism_report_to_be_uploaded()
    submission_to_update = Submission.objects.plagiarism_report_to_be_updated()

    for submission in submissions_to_upload:
        report, __ = iThenticate.objects.get_or_create(to_submission=submission)
        # do it...

    for submission in submission_to_update:
        report = submission.plagiarism_report
        # do it...
