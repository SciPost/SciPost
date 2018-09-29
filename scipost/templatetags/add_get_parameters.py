__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def add_get_parameters(context, **kwargs):
    parameters = context['request'].GET.copy()
    for k, v in kwargs.items():
        if v is not None:
            parameters[k] = v
    if parameters:
        params = '?'
        for k, v in parameters.items():
            params += '&%s=%s' % (k, v)
        return params.replace('?&', '?')
    return ''
