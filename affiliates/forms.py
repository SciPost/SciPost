__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.contrib.auth.models import User

from dal import autocomplete


class AddAffiliateJournalManagerForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='/user-autocomplete',
            attrs={'data-html': True}
        ),
        label='',
        required=True
    )
