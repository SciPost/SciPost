__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import copy
from django import forms
from crispy_forms.helper import FormHelper
from django.core.validators import EmailValidator


class HTMXInlineCRUDModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper() if not hasattr(self, "helper") else self.helper
        self.helper.form_tag = False


class ModelChoiceFieldwithid(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s (id = %i)" % (super().label_from_instance(obj), obj.id)


class MultiEmailValidator(EmailValidator):
    def __call__(self, mail_str: str):
        for email in mail_str.split(","):
            super().__call__(email.strip())


# Should not be an Email field because browser validation is unwanted.
class MultiEmailField(forms.CharField):
    default_validators = [MultiEmailValidator()]


##### HTMX Class Based Forms #####
class HTMXDynSelWidget(forms.Select):
    template_name = "htmx/dynsel.html"

    def __init__(self, attrs=None, choices=(), **kwargs):
        self.url = kwargs.pop("url", {})
        super().__init__(attrs, choices, **kwargs)

        self.attrs = self.attrs | {
            "onclick": "return false;",
            "onkeydown": "return false;",
            "tabindex": "-1",
        }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["url"] = self.url
        return context

    def filter_choices_to_render(self, selected_choices):
        """Replace self.choices with selected_choices."""
        if hasattr(self.choices, "queryset"):
            try:
                self.choices.queryset = self.choices.queryset.filter(
                    pk__in=[c for c in selected_choices if c]
                )
            except ValueError:
                # if selected_choices are invalid, do nothing
                pass
        else:
            self.choices = [c for c in self.choices if str(c[0]) in selected_choices]

    def optgroups(self, name, value, attrs=None):
        """
        Exclude unselected self.choices before calling the parent method.

        Used by Django>=1.10.
        """
        # Filter out None values, not needed for autocomplete
        selected_choices = [str(c) for c in value if c]
        all_choices = copy.copy(self.choices)

        self.filter_choices_to_render(selected_choices)

        result = super().optgroups(name, value, attrs)
        self.choices = all_choices

        return result
