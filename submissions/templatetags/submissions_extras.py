from django import template
from django.utils import timezone

from submissions.models import SUBMISSION_STATUS_OUT_OF_POOL
from submissions.models import Submission

register = template.Library()

@register.filter(name='is_not_author_of_submission')
def is_not_author_of_submission(user, arxiv_identifier_w_vn_nr):
    submission = Submission.objects.get(arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    return (user.contributor not in submission.authors.all()
            and
            (user.last_name not in submission.author_list
             or
             user.contributor in submission.authors_false_claims.all() ) )


@register.filter(name='is_viewable_by_authors')
def is_viewable_by_authors(recommendation):
    return recommendation.submission.status in ['revision_requested', 'resubmitted',
                                                'accepted', 'rejected',
                                                'published', 'withdrawn']

@register.filter(name='required_actions')
def required_actions(submission):
    """
    This method returns a list of required actions on a Submission.
    Each list element is a textual statement.
    """
    if submission.status in SUBMISSION_STATUS_OUT_OF_POOL:
        return []
    todo = []
    for comment in submission.comment_set.all():
        if comment.status == 0:
            todo.append('A Comment from %s has been delivered but is not yet vetted. '
                        'Please vet it.' % comment.author)
    nr_ref_inv = submission.refereeinvitation_set.count()
    if nr_ref_inv == 0:
        todo.append('No Referees have yet been invited. '
                    'At least 3 should be.')
    elif nr_ref_inv < 3:
        todo.append('Only %s Referees have been invited. '
                    'At least 3 should be.' % nr_ref_inv)
    for ref_inv in submission.refereeinvitation_set.all():
        refname = ref_inv.last_name + ', ' + ref_inv.last_name
        if ref_inv.referee:
            refname = str(ref_inv.referee)
        if ref_inv.accepted is None and not ref_inv.cancelled:
            todo.append('Referee %s has not yet responded. Consider sending a reminder '
                        'or cancelling the invitation.' % refname)
        if ref_inv.accepted and not ref_inv.fulfilled and not ref_inv.cancelled:
            todo.append('Referee %s has accepted to send a Report, '
                        'but not yet delivered it. Consider sending a '
                        'reminder.' % refname)
    if submission.reporting_deadline < timezone.now():
        todo.append('The refereeing deadline has passed. Please either extend it, '
                    'or formulate your Editorial Recommendation.')
    reports = submission.report_set.all()
    for report in reports:
        if report.status == 0:
            todo.append('The Report from %s has been delivered but is not yet vetted. '
                        'Please vet it.' % report.author)
    return todo
