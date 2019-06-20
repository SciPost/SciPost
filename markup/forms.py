__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .utils import process_markup


class MarkupTextForm(forms.Form):
    markup_text = forms.CharField()

    def get_processed_markup(self):
        return process_markup(self.cleaned_data['markup_text'])
