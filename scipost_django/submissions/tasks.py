__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from datetime import timedelta
from difflib import SequenceMatcher

from django.utils import timezone

from SciPost_v1.celery import app

from .models import Submission, EditorialAssignment, RefereeInvitation, Report

from journals.models import Publication


@app.task(bind=True)
def send_editorial_assignment_invitations(self):
    """
    Send next queued editorial assignment invitation emails.
    """
    qs = Submission.objects.seeking_assignment().has_editor_invitations_to_be_sent().distinct()
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


@app.task(bind=True)
def check_for_internal_plagiarism_submission_matches(self, ratio_threshold=0.7):
    """
    Check Submissions for internal plagiarism with preexisting Submissions.
    """

    submissions_to_check = Submission.objects.exclude(
        internal_plagiarism_matches__has_key="submission_matches"
    )

    # Check in small batches to not overwhelm the server
    for sub_to_check in submissions_to_check.all()[:5]:
        submission_matches = []
        # check all Submissions which predate, and are not in the thread of the sub
        for sub in Submission.objects.exclude(
                thread_hash=sub_to_check.thread_hash
        ).filter(submission_date__lt=sub_to_check.submission_date):
            sub_title_sm = SequenceMatcher(None, sub_to_check.title, sub.title)
            ratio_title = sub_title_sm.ratio()
            ratio_authors = SequenceMatcher(
                None, sub_to_check.author_list, sub.author_list
            ).ratio()
            ratio_abstract = SequenceMatcher(
                None, sub_to_check.abstract, sub.abstract
            ).ratio()
            if ratio_title > ratio_threshold or ratio_abstract > ratio_threshold:
                submission_matches.append(
                    {
                        "identifier_w_vn_nr": sub.preprint.identifier_w_vn_nr,
                        "ratio_title": ratio_title,
                        "ratio_authors": ratio_authors,
                        "ratio_abstract": ratio_abstract,
                    }
                )
        sub_to_check.internal_plagiarism_matches["submission_matches"] = submission_matches
        sub_to_check.save()


@app.task(bind=True)
def check_for_internal_plagiarism_publication_matches(self, ratio_threshold=0.7):
    """
    Check Submissions for internal plagiarism with existing Publications.
    """

    submissions_to_check = Submission.objects.exclude(
        internal_plagiarism_matches__has_key="publication_matches"
    )

    # Check in small batches to not overwhelm the server
    for sub_to_check in submissions_to_check.all()[:5]:
        publication_matches = []
        for pub in Publication.objects.filter(publication_date__lt=sub_to_check.submission_date):
            ratio_title = SequenceMatcher(None, sub_to_check.title, pub.title).ratio()
            ratio_authors = SequenceMatcher(
                None, sub_to_check.author_list, pub.author_list
            ).ratio()
            ratio_abstract = SequenceMatcher(
                None, sub_to_check.abstract, pub.abstract
            ).ratio()
            if ratio_title > ratio_threshold or ratio_abstract > ratio_threshold:
                publication_matches.append(
                    {
                        "doi_label": pub.doi_label,
                        "ratio_title": ratio_title,
                        "ratio_authors": ratio_authors,
                        "ratio_abstract": ratio_abstract,
                    }
                )
        sub_to_check.internal_plagiarism_matches["publication_matches"] = publication_matches
        sub_to_check.save()
