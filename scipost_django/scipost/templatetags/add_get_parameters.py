__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def add_get_parameters(context, **kwargs):
    parameters = context["request"].GET.copy()
    for k, v in kwargs.items():
        if v is not None:
            parameters[k] = v
        elif k in parameters.keys():
            del parameters[k]
    if parameters:
        params = "?"
        for k, v in parameters.items():
            if k != "page":  # remove any pagination
                params += "&%s=%s" % (k, v)
        return params.replace("?&", "?")  # remove extra & of first parameter
    return ""
