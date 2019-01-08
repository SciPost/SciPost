__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..constants import PROSPECTIVE_PARTNER_REQUESTED,\
                        PROSPECTIVE_PARTNER_ADDED,\
                        PROSPECTIVE_PARTNER_APPROACHED,\
                        PROSPECTIVE_PARTNER_NEGOTIATING,\
                        PROSPECTIVE_PARTNER_UNINTERESTED,\
                        PROSPECTIVE_PARTNER_PROCESSED,\
                        PROSPECTIVE_PARTNER_FOLLOWED_UP

register = template.Library()


@register.filter(name='partnerstatuscolor')
def partnerstatuscolor(status):
    color = '#333333'
    if status == PROSPECTIVE_PARTNER_REQUESTED:
        color = '#3399ff'
    elif status == PROSPECTIVE_PARTNER_ADDED:
        color = '#6699cc'
    elif status == PROSPECTIVE_PARTNER_APPROACHED:
        color = '#ffcc33'
    elif status == PROSPECTIVE_PARTNER_NEGOTIATING:
        color = '#ff8c00'
    elif status == PROSPECTIVE_PARTNER_UNINTERESTED:
        color = '#ee0000'
    elif status == PROSPECTIVE_PARTNER_PROCESSED:
        color = '#32cd32'
    elif status == PROSPECTIVE_PARTNER_FOLLOWED_UP:
        color = '#d2e3f6'
    return color


@register.filter(name='pubfractions_in_year')
def pubfractions_in_year(org, year):
    return org.pubfractions_in_year(int(year))
