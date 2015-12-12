from django import forms

from .models import *


class RatingForm(forms.Form):
    """ Abstract base class for all rating forms. """
    clarity = forms.ChoiceField(RATING_CHOICES)
    validity = forms.ChoiceField(RATING_CHOICES)
    rigour = forms.ChoiceField(RATING_CHOICES)
    originality = forms.ChoiceField(RATING_CHOICES)
    significance = forms.ChoiceField(RATING_CHOICES)

    class Meta:
        abstract = True


class CommentaryRatingForm(RatingForm):
    pass


class CommentRatingForm(RatingForm):
    pass


class AuthorReplyRatingForm(RatingForm):
    pass


class SubmissionRatingForm(RatingForm):
    pass


class ReportRatingForm(RatingForm):
    pass
