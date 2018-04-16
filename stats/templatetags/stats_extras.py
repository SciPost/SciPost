__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


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
    """Return a sorted list of active years of the Journal."""
    years = []
    if journal.has_volumes:
        years = journal.volumes.dates('until_date', 'year')
    else:
        years = journal.publications.dates('publication_date', 'year')
    return [x.year for x in years]
