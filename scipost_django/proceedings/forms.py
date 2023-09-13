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
            "logo",
            "cover_image",
            "picture",
            "picture_credit",
            "preface_title",
            "preface_text",
        )
        widgets = {
            "submissions_open": forms.DateInput(attrs={"type": "date"}),
            "submissions_deadline": forms.DateInput(attrs={"type": "date"}),
            "submissions_close": forms.DateInput(attrs={"type": "date"}),
            "event_start_date": forms.DateInput(attrs={"type": "date"}),
            "event_end_date": forms.DateInput(attrs={"type": "date"}),
        }
        help_texts = {
            "logo": "Upload a logo for the proceedings.",
            "cover_image": "Upload a cover image, e.g. the first cover page of the issue, for the proceedings.",
            "picture": "Upload a centered picture for the proceedings.",
            "preface_text": "HTML content of the preface.",
        }
