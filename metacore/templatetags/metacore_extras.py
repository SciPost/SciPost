__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

register = template.Library()


@register.filter
def join_authors_list(authors, max_n=None):
    """ Returns authors list as string, truncated to max_n authors when the list is longer."""
    if max_n and max_n < len(authors):
        return ', '.join(authors[:max_n - 1]) + ' ... ' + authors[-1]
    elif len(authors) > 1:
        return ', '.join(authors[:-1]) + ' and ' + authors[-1]
    return authors[0]
