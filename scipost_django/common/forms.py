__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


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
class HTMXDynSelWidget(forms.Widget):
    template_name = "htmx/dynsel.html"

    def __init__(self, *args, **kwargs):
        self.dynsel_context = kwargs.pop("dynsel_context", {})
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["dynsel_context"] = self.dynsel_context
        return context
