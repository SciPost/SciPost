__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import Proceedings


class ProceedingsForm(forms.ModelForm):
    class Meta:
        model = Proceedings
        fields = (
            "issue",
            "minimum_referees",
            "event_name",
            "event_suffix",
            "event_description",
            "event_start_date",
            "event_end_date",
            "submissions_open",
            "submissions_deadline",
            "submissions_close",
            "template_latex_tgz",
        )


class ProceedingsMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.event_suffix or obj.event_name
