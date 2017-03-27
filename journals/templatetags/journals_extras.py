from django import template

from journals.helpers import paper_nr_string

register = template.Library()


@register.filter(name='paper_nr_string_filter')
def paper_nr_string_filter(nr):
    return paper_nr_string(nr)
