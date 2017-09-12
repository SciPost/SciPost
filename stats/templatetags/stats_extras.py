from django import template
from django.db.models import Avg, F

from journals.models import Publication
from submissions.constants import SUBMISSION_STATUS_OUT_OF_POOL
from submissions.models import Submission

register = template.Library()



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


@register.filter(name='journal_nr_publications')
def journal_nr_publications(journal):
    return Publication.objects.filter(in_issue__in_volume__in_journal=journal).count()


@register.filter(name='journal_avg_processing_duration')
def journal_avg_processing_duration(journal):
    duration = Publication.objects.filter(
        in_issue__in_volume__in_journal=journal).aggregate(
            avg=Avg(F('publication_date') - F('submission_date')))['avg']
    if not duration: return 0
    return duration.days + duration.seconds/86400


@register.filter(name='volume_nr_publications')
def volume_nr_publications(volume):
    return Publication.objects.filter(in_issue__in_volume=volume).count()


@register.filter(name='volume_avg_processing_duration')
def volume_avg_processing_duration(volume):
    duration = Publication.objects.filter(
        in_issue__in_volume=volume).aggregate(
            avg=Avg(F('publication_date') - F('submission_date')))['avg']
    if not duration: return 0
    return duration.days + duration.seconds/86400


@register.filter(name='issue_nr_publications')
def issue_nr_publications(issue):
    return Publication.objects.filter(in_issue=issue).count()


@register.filter(name='issue_avg_processing_duration')
def issue_avg_processing_duration(issue):
    duration = Publication.objects.filter(
        in_issue=issue).aggregate(
            avg=Avg(F('publication_date') - F('submission_date')))['avg']
    if not duration: return 0
    return duration.days + duration.seconds/86400
