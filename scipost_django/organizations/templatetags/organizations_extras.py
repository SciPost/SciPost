__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

register = template.Library()


@register.filter(name="pubfrac_for_publication")
def pubfrac_for_publication(org, publication):
    return org.pubfrac_for_publication(publication.doi_label)


@register.filter(name="expenditure_for_publication")
def expenditure_for_publication(org, publication):
    if publication.doi_label in org.cf_expenditure_for_publication:
        return org.cf_expenditure_for_publication[publication.doi_label]["expenditure"]


@register.filter(name="pubfracs_in_year")
def pubfracs_in_year(org, year):
    fractions = org.pubfracs_in_year(int(year))
    return fractions["total"] or "0"
