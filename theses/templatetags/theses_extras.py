from django import template

from scipost.constants import SCIPOST_DISCIPLINES, subject_areas_dict, disciplines_dict

register = template.Library()


@register.filter
def type(thesislink):
    return thesislink.THESIS_TYPES_DICT[thesislink.type]


@register.filter
def discipline(thesislink):
    return disciplines_dict[thesislink.discipline]


@register.filter
def domain(thesislink):
    return thesislink.get_domain_display


@register.filter
def subject_area(thesislink):
    return subject_areas_dict[thesislink.subject_area]
