__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

register = template.Library()


@register.simple_tag
def avg_processing_duration(obj, *args, **kwargs):
    return getattr(obj, "avg_processing_duration")(*args, **kwargs)


@register.simple_tag
def nr_publications(obj, *args, **kwargs):
    return getattr(obj, "nr_publications")(*args, **kwargs)


@register.simple_tag
def citation_rate(obj, *args, **kwargs):
    return getattr(obj, "citation_rate")(*args, **kwargs)


@register.filter(name="submissions_count_distinct")
def submissions_count_distinct(submissions):
    thread_hashes = []
    for submission in submissions:
        if submission.thread_hash not in thread_hashes:
            thread_hashes.append(submission.thread_hash)
    return len(thread_hashes)


@register.filter(name="journal_publication_years")
def journal_publication_years(journal):
    """Return a sorted list of active years of the Journal."""
    years = []
    if journal.has_volumes:
        years = journal.volumes.dates("until_date", "year")
    else:
        years = journal.publications.dates("publication_date", "year")
    return [x.year for x in years]
