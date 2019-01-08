__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..constants import (
    POTENTIAL_FELLOWSHIP_IDENTIFIED, POTENTIAL_FELLOWSHIP_INVITED, POTENTIAL_FELLOWSHIP_REINVITED,
    POTENTIAL_FELLOWSHIP_MULTIPLY_REINVITED, POTENTIAL_FELLOWSHIP_DECLINED,
    POTENTIAL_FELLOWSHIP_UNRESPONSIVE, POTENTIAL_FELLOWSHIP_RETIRED, POTENTIAL_FELLOWSHIP_DECEASED,
    POTENTIAL_FELLOWSHIP_INTERESTED, POTENTIAL_FELLOWSHIP_REGISTERED,
    POTENTIAL_FELLOWSHIP_ACTIVE_IN_COLLEGE, POTENTIAL_FELLOWSHIP_SCIPOST_EMERITUS
    )

from common.utils import hslColorWheel


register = template.Library()


@register.filter(name='potfelstatuscolor')
def potfelstatuscolor(status):
    color = '#333333'
    if status == POTENTIAL_FELLOWSHIP_IDENTIFIED:
        color = hslColorWheel(12, 8)
    elif status == POTENTIAL_FELLOWSHIP_INVITED:
        color = hslColorWheel(12, 9)
    elif status == POTENTIAL_FELLOWSHIP_REINVITED:
        color = hslColorWheel(12, 10)
    elif status == POTENTIAL_FELLOWSHIP_MULTIPLY_REINVITED:
        color = hslColorWheel(12, 11)
    elif status == POTENTIAL_FELLOWSHIP_DECLINED:
        color = hslColorWheel(12, 0)
    elif status == POTENTIAL_FELLOWSHIP_UNRESPONSIVE:
        color = hslColorWheel(12, 1)
    elif status == POTENTIAL_FELLOWSHIP_RETIRED:
        color = hslColorWheel(12, 1, 75)
    elif status == POTENTIAL_FELLOWSHIP_DECEASED:
        color = hslColorWheel(12, 1, 10)
    elif status == POTENTIAL_FELLOWSHIP_INTERESTED:
        color = hslColorWheel(12, 2)
    elif status == POTENTIAL_FELLOWSHIP_REGISTERED:
        color = hslColorWheel(12, 3)
    elif status == POTENTIAL_FELLOWSHIP_ACTIVE_IN_COLLEGE:
        color = hslColorWheel(12, 4)
    elif status == POTENTIAL_FELLOWSHIP_SCIPOST_EMERITUS:
        color = hslColorWheel(12, 4, 40, 40)
    return color
