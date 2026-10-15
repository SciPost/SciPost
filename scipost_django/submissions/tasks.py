__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from difflib import SequenceMatcher

from django.utils import timezone
from journals.models import Publication
from requests import HTTPError
from SciPost_v1.celery import app
from submissions.constants import STATUS_FAILED_UPLOAD, STATUS_REQUESTED, STATUS_SENT
from submissions.models import Submission, iThenticateReport
from .plagiarism import SciPostiThenticateService


@app.task(autoretry_for=(HTTPError,), retry_backoff=True)
def create_iThenticate_submission(scipost_submission_id: int):
    """Create a new iThenticate submission for a SciPost Submission."""
    # Create the iThenticate submission for the Submission
    service = SciPostiThenticateService()
    submission = Submission.objects.get(id=scipost_submission_id)
    tca_sub = service.tca_submission_from_submission(submission)
    if tca_sub.group:
        tca_sub.group.update()
    tca_sub.create()

    # Store the iThenticate submission ID in a preliminary iThenticateReport object
    raw_sub_info = tca_sub.get()
    report_data = {
        "created_time": tca_sub.created_time,
        "submission_raw_data": raw_sub_info,
    }
    report, __ = iThenticateReport.objects.update_or_create(
        to_submission=submission,
        defaults=report_data,
        create_defaults=report_data | {"sub_id": tca_sub.id},
    )

    # Upload the Submission document to iThenticate
    document_bytes = submission.preprint.get_document()
    document_filename = submission.title + ".pdf"
    try:
        tca_sub.upload_document(document_bytes, document_filename)
        report.status = STATUS_SENT
        report.uploaded_time = timezone.now()
        report.save()
    except HTTPError as e:
        report.status = STATUS_FAILED_UPLOAD
        report.save()
        raise e


@app.task(autoretry_for=(HTTPError,), retry_backoff=True)
def request_iThenticate_report(scipost_submission_id: int):
    """Request a plagiarism report from iThenticate for a SciPost Submission."""
    service = SciPostiThenticateService()

    submission = Submission.objects.get(id=scipost_submission_id)
    try:
        report = submission.iThenticate_plagiarism_report
    except iThenticateReport.DoesNotExist:
        raise ValueError(
            f"No iThenticateReport found for Submission ID {scipost_submission_id}"
        )

    # Request the report from iThenticate
    tca_report = report.tca_report
    tca_report.set_client(service.client)
    tca_report.generate(
        params={
            "generation_settings": {
                "search_repositories": [sr.value for sr in service.search_repositories]
            }
        }
    )

    report.requested_time = timezone.now()
    report.status = STATUS_REQUESTED
    report.save()


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
        sub_to_check.internal_plagiarism_matches["submission_matches"] = (
            submission_matches
        )
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
        for pub in Publication.objects.filter(
            publication_date__lt=sub_to_check.submission_date
        ):
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
        sub_to_check.internal_plagiarism_matches["publication_matches"] = (
            publication_matches
        )
        sub_to_check.save()
