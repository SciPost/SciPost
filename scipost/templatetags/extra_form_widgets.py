from django import template

from ..widgets import SelectButtonWidget


register = template.Library()


@register.filter
def checkboxes_as_btn(field):
    w = field.field.widget
    return field.as_widget(SelectButtonWidget(attrs=w.attrs, choices=w.choices))
