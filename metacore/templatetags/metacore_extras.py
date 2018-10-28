from django import template

register = template.Library()


@register.filter
def truncate_list(authors, max_n):
    """ Returns author list, truncated to max_n authors when the list is longer """
    if max_n and max_n < len(authors):
        return '; '.join(authors[:max_n]) + ' et al.'
    else:
        return '; '.join(authors)
