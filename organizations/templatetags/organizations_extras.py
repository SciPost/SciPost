__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

register = template.Library()


@register.filter(name='pubfraction_for_publication')
def pubfraction_for_publication(org, publication):
    return org.pubfraction_for_publication(publication.doi_label)

@register.filter(name='pubfractions_in_year')
def pubfractions_in_year(org, year):
    return org.pubfractions_in_year(int(year))
