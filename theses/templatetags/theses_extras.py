from django import template

register = template.Library()


@register.filter
def type(thesislink):
    # deprecated method, to be removed in future
    return thesislink.get_type_display()


@register.filter
def discipline(thesislink):
    # deprecated method, to be removed in future
    return thesislink.get_discipline_display()


@register.filter
def domain(thesislink):
    # deprecated method, to be removed in future
    return thesislink.get_domain_display()


@register.filter
def subject_area(thesislink):
    # deprecated method, to be removed in future
    return thesislink.get_subject_area_display()
