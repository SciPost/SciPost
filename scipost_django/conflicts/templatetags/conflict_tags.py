__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template
from django.db.models import Q

register = template.Library()


@register.filter
def filter_for_contributor(qs, contributor):
    """Filter ConflictOfInterest query for specific Contributor."""
    return qs.filter(
        Q(profile__contributor=contributor)
        | Q(related_profile__contributor=contributor)
    ).distinct()


@register.filter
def filter_for_submission(qs, submission):
    """Filter ConflictOfInterest query for specific Submission."""
    authors = submission.authors.all()
    return qs.filter(
        Q(related_submissions=submission)
        | Q(profile__contributor__in=authors)
        | Q(related_profile__contributor__in=authors)
    ).distinct()
