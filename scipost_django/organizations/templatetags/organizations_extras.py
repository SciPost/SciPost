__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

register = template.Library()


@register.filter(name="pubfraction_for_publication")
def pubfraction_for_publication(org, publication):
    return org.pubfraction_for_publication(publication.doi_label)


@register.filter(name="pubfractions_in_year")
def pubfractions_in_year(org, year):
    fractions = org.pubfractions_in_year(int(year))
    if not fractions["total"]:
        return "total: 0"
    text = "total: %s" % fractions["total"]
    if fractions["confirmed"] == fractions["total"]:
        text += " (confirmed)"
        return text
    elif fractions["estimated"] == fractions["total"]:
        text += " (estimated)"
        return text
    text += " (confirmed: %s; estimated: %s)" % (
        fractions["confirmed"],
        fractions["estimated"],
    )
    return text
