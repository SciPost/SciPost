__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import Feedback, Nomination, Motion

from scipost.constants import SCIPOST_SUBJECT_AREAS


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['feedback']


class NominationForm(forms.ModelForm):
    class Meta:
        model = Nomination
        fields = ['first_name', 'last_name',
                  'discipline', 'expertises', 'webpage']

    def __init__(self, *args, **kwargs):
        super(NominationForm, self).__init__(*args, **kwargs)
        self.fields['expertises'].widget = forms.SelectMultiple(choices=SCIPOST_SUBJECT_AREAS)


class MotionForm(forms.ModelForm):
    class Meta:
        model = Motion
        fields = ['category', 'background', 'motion']

    def __init__(self, *args, **kwargs):
        super(MotionForm, self).__init__(*args, **kwargs)
        self.fields['background'].label = ''
        self.fields['background'].widget.attrs.update(
            {'rows': 8, 'cols': 100,
             'placeholder': 'Provide useful background information on your Motion.'})
        self.fields['motion'].label = ''
        self.fields['motion'].widget.attrs.update(
            {'rows': 8, 'cols': 100,
             'placeholder': 'Phrase your Motion as clearly and succinctly as possible.'})
