from django import template
from django.db.models import Avg, F

from journals.models import Publication
from submissions.constants import SUBMISSION_STATUS_OUT_OF_POOL
from submissions.models import Submission

register = template.Library()



@register.simple_tag
def avg_processing_duration(obj, *args, **kwargs):
    method = getattr(obj, avg_processing_duration)
    return method(*args, **kwargs)

@register.simple_tag
def nr_publications(obj, *args, **kwargs):
    method = getattr(obj, nr_publications)
    return method(*args, **kwargs)

@register.simple_tag
def citation_rate(obj, *args, **kwargs):
    method = getattr(obj, citation_rate)
    return method(*args, **kwargs)


@register.filter(name='submissions_count_distinct')
def submissions_count_distinct(submissions):
    identifiers_wo_vn_nr = []
    for submission in submissions:
        if submission.arxiv_identifier_wo_vn_nr not in identifiers_wo_vn_nr:
            identifiers_wo_vn_nr.append(submission.arxiv_identifier_wo_vn_nr)
    return len(identifiers_wo_vn_nr)


@register.filter(name='journal_publication_years')
def journal_publication_years(journal):
    years = []
    for volume in journal.volume_set.all():
        if volume.until_date.year not in years:
            years.append(volume.until_date.year)
    return sorted(years)
