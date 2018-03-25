__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

register = template.Library()


@register.filter
def has_all_author_relations(publication):
    """
    Check if all authors are added to the Publication object, just by counting.
    """
    return len(publication.author_list.split(',')) == publication.authors.count()
