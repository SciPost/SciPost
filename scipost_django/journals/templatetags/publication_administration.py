__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from journals.models.publication import Publication

register = template.Library()


@register.filter
def has_all_author_relations(publication: Publication) -> bool:
    """
    Check if all authors are added to the Publication object, just by counting.
    """
    submission_string_authors = publication.author_list.split(",")
    associated_authors = publication.authors.filter(profile__isnull=False) # exclude temp authors without profiles

    return len(submission_string_authors) == associated_authors.count()

@register.filter
def author_affiliations_complete(publication: Publication) -> bool:
    """
    Checks if each author has a non-empty affiliations field.
    """
    if not has_all_author_relations(publication):
        return False
    for author in publication.authors.all():
        if not author.affiliations.exists():
            return False
    return True
