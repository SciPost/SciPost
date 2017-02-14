from django import forms
from django.template import Context
from django.template.loader import get_template
from django import template


register = template.Library()

# Custom filter originally created by tzangms
#  and customized for use with Bootstrap 4.x
#  https://github.com/tzangms/django-bootstrap-form


@register.filter
def bootstrap(element, args='2,10'):
    '''Pass arguments to tag by separating them using a comma ",".

    Arguments:
    -- 1. Column width for label
    -- 2. Column width for input
    -- 3. Additional argument 'sm' or 'lg' for form groups.
    '''
    args = [arg.strip() for arg in args.split(',')]
    markup_classes = {
        'label': 'col-md-%s' % args[0],
        'value': 'col-md-%s' % args[1],
        'single_value': ''
    }
    try:
        markup_classes['label'] += ' col-form-label-%s' % args[2]
        markup_classes['form_control'] = 'form-control-%s' % args[2]
    except IndexError:
        markup_classes['form_control'] = ''
    return render(element, markup_classes)


@register.filter
def bootstrap_inline(element):
    markup_classes = {'label': 'sr-only', 'value': '', 'single_value': ''}
    return render(element, markup_classes)


@register.filter
def add_input_classes(field, extra_classes=''):
    if not is_checkbox(field) and not is_multiple_checkbox(field) \
       and not is_radio(field) and not is_file(field):
        field_classes = field.field.widget.attrs.get('class', '')
        field_classes += ' form-control ' + extra_classes
        field.field.widget.attrs['class'] = field_classes


def render(element, markup_classes):
    element_type = element.__class__.__name__.lower()

    if element_type == 'boundfield':
        add_input_classes(element, markup_classes['form_control'])
        template = get_template("tags/bootstrap/field.html")
        context = Context({'field': element, 'classes': markup_classes, 'form': element.form})
    else:
        has_management = getattr(element, 'management_form', None)
        if has_management:
            for form in element.forms:
                for field in form.visible_fields():
                    add_input_classes(field, markup_classes['form_control'])

            template = get_template("tags/bootstrap/formset.html")
            context = Context({'formset': element, 'classes': markup_classes})
        else:
            for field in element.visible_fields():
                add_input_classes(field, markup_classes['form_control'])

            template = get_template("tags/bootstrap/form.html")
            context = Context({'form': element, 'classes': markup_classes})

    return template.render(context)


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxInput)


@register.filter
def is_multiple_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxSelectMultiple)


@register.filter
def is_radio(field):
    return isinstance(field.field.widget, forms.RadioSelect)


@register.filter
def is_file(field):
    return isinstance(field.field.widget, forms.FileInput)
