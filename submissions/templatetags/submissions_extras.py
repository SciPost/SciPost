__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from submissions.models import Submission

register = template.Library()


@register.filter(name='is_not_author_of_submission')
def is_not_author_of_submission(user, arxiv_identifier_w_vn_nr):
    submission = Submission.objects.get(arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    return (user.contributor not in submission.authors.all()
            and
            (user.last_name not in submission.author_list
             or
             user.contributor in submission.authors_false_claims.all()))


@register.filter(name='is_viewable_by_authors')
def is_viewable_by_authors(recommendation):
    return recommendation.submission.status in ['revision_requested', 'resubmitted',
                                                'accepted', 'rejected',
                                                'published', 'withdrawn']


@register.filter
def user_is_referee(submission, user):
    if not user.is_authenticated:
        return False
    return submission.referee_invitations.filter(referee__user=user).exists()


@register.filter
def is_voting_fellow(submission, user):
    if not user.is_authenticated:
        return False
    return submission.voting_fellows.filter(contributor__user=user).exists()


@register.filter
def citation(citable):
    return citable.citation
