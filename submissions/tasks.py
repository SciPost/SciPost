__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from SciPost_v1.celery import app

from .models import Submission, EditorialAssignment


@app.task(bind=True)
def send_editorial_assignment_invitations(self):
    """Send invitation email to 'next EditorialAssignment' in que."""
    qs = Submission.objects.unassigned().has_editor_invitations_to_be_sent().distinct()
    submission_ids = qs.values_list('id', flat=True)
    submissions_count = len(submission_ids)

    count = 0
    for submission_id in submission_ids:
        self.update_state(
            state="PROGRESS", meta={
                'progress': round(100 * count / submissions_count),
                'total_count': submissions_count,
            })

        # Get EditorialAssignment to send or nothing.
        ed_assignment = EditorialAssignment.objects.next_invitation_to_be_sent(submission_id)
        if ed_assignment:
            if ed_assignment.send_invitation():
                count += 1
    return {'new_invites': count}
