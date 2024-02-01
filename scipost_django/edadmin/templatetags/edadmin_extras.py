__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

register = template.Library()


@register.simple_tag
def activity_level_bg_color(nr_total: int, nr_done: int):
    """
    Return a background color class depending on percentage done.
    """
    if nr_total == 0 or nr_total == nr_done:
        return "bg-success"
    elif 4 * nr_done > 3 * nr_total:
        return "bg-opacity-75 bg-success"
    elif 2 * nr_done > nr_total:
        return "bg-opacity-50 bg-success"
    elif nr_done > 0:
        return "bg-warning"
    else:
        return "bg-danger"
