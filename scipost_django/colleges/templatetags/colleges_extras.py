__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template
from django.utils.html import format_html, mark_safe

from ..constants import (
    POTENTIAL_FELLOWSHIP_IDENTIFIED, POTENTIAL_FELLOWSHIP_NOMINATED,
    POTENTIAL_FELLOWSHIP_ELECTION_VOTE_ONGOING,
    POTENTIAL_FELLOWSHIP_ELECTED, POTENTIAL_FELLOWSHIP_NOT_ELECTED,
    POTENTIAL_FELLOWSHIP_INVITED, POTENTIAL_FELLOWSHIP_REINVITED,
    POTENTIAL_FELLOWSHIP_MULTIPLY_REINVITED, POTENTIAL_FELLOWSHIP_DECLINED,
    POTENTIAL_FELLOWSHIP_UNRESPONSIVE, POTENTIAL_FELLOWSHIP_RETIRED, POTENTIAL_FELLOWSHIP_DECEASED,
    POTENTIAL_FELLOWSHIP_INTERESTED, POTENTIAL_FELLOWSHIP_REGISTERED,
    POTENTIAL_FELLOWSHIP_ACTIVE_IN_COLLEGE, POTENTIAL_FELLOWSHIP_SCIPOST_EMERITUS
    )
from ..models import Fellowship

from common.utils import hslColorWheel


register = template.Library()


@register.filter(name='potfelstatuscolor')
def potfelstatuscolor(status):
    color = '#333333'
    if status == POTENTIAL_FELLOWSHIP_IDENTIFIED:
        color = hslColorWheel(12, 8)
    elif status == POTENTIAL_FELLOWSHIP_NOMINATED:
        color = 'Orange'
    elif status == POTENTIAL_FELLOWSHIP_ELECTION_VOTE_ONGOING:
        color = 'DodgerBlue'
    elif status == POTENTIAL_FELLOWSHIP_ELECTED:
        color = 'MediumSeaGreen'
    elif status == POTENTIAL_FELLOWSHIP_NOT_ELECTED:
        color = 'Tomato'
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


@register.simple_tag
def voting_results_display(potfel):
    if potfel.status == POTENTIAL_FELLOWSHIP_ELECTION_VOTE_ONGOING:
        nr_agree = potfel.in_agreement.count()
        nr_abstain = potfel.in_abstain.count()
        nr_disagree = potfel.in_disagreement.count()
        specialties_slug_list = [s.slug for s in potfel.profile.specialties.all()]
        nr_spec_agree = potfel.in_agreement.all(
        ).specialties_overlap(specialties_slug_list).count()
        nr_spec_abstain = potfel.in_abstain.all(
        ).specialties_overlap(specialties_slug_list).count()
        nr_spec_disagree = potfel.in_disagreement.all(
        ).specialties_overlap(specialties_slug_list).count()
        nr_specialists = Fellowship.objects.senior().active(
        ).specialties_overlap(specialties_slug_list).count()
        nr_Fellows = potfel.college.fellowships.senior().active().count()
        # Establish whether election criterion has been met.
        # Rule is: spec Agree must be > half of (total nr of spec - nr abstain)
        election_agree_percentage = int(
            100 * nr_spec_agree/(max(1, nr_specialists - nr_spec_abstain)))
        election_criterion_met = nr_spec_agree > 0 and election_agree_percentage > 50
        if election_criterion_met:
            election_text = ('&emsp;<strong class="bg-success p-1 text-white">'
                             'Elected (%s&#37; in favour)</strong>' % str(election_agree_percentage))
        else:
            election_text = ('&emsp;<strong class="bg-warning p-1 text-white">'
                             '%s&#37; in favour</strong>') % str(election_agree_percentage)
        return format_html('Specialist Senior Fellows ({}):<br/>Agree: {}, Abstain: {}, Disagree: {}&nbsp;{}<br/>'
                           'All: ({} Fellows)<br/>Agree: {}, Abstain: {}, Disagree: {}',
                           nr_specialists, nr_spec_agree, nr_spec_abstain, nr_spec_disagree,
                           mark_safe(election_text),
                           nr_Fellows, nr_agree, nr_abstain, nr_disagree)
    return ''
