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


@register.filter
def authors_in_right_order(publication):
    """
    Checks if all author orderings correspond to those in author list.
    """
    if not has_all_author_relations(publication):
        return False
    list_of_authors = publication.author_list.split(',')
    for author in publication.authors.all():
        if author.last_name not in list_of_authors[author.order]:
            return False
    return True
