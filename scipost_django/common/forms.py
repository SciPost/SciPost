__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from crispy_forms.helper import FormHelper


class HTMXInlineCRUDModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper() if not hasattr(self, "helper") else self.helper
        self.helper.form_tag = False


class ModelChoiceFieldwithid(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s (id = %i)" % (super().label_from_instance(obj), obj.id)
