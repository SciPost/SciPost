from django import template

register = template.Library()


@register.simple_tag
def avg_processing_duration(obj, *args, **kwargs):
    return getattr(obj, 'avg_processing_duration')(*args, **kwargs)


@register.simple_tag
def nr_publications(obj, *args, **kwargs):
    return getattr(obj, 'nr_publications')(*args, **kwargs)


@register.simple_tag
def citation_rate(obj, *args, **kwargs):
    return getattr(obj, 'citation_rate')(*args, **kwargs)


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
