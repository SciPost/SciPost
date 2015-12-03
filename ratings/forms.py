from django import forms

from .models import *


class CommentaryRatingForm(forms.Form):
    clarity = forms.ChoiceField(RATING_CHOICES)
    correctness = forms.ChoiceField(RATING_CHOICES)
    usefulness = forms.ChoiceField(RATING_CHOICES)


class CommentRatingForm(forms.Form):
    clarity = forms.ChoiceField(RATING_CHOICES)
    correctness = forms.ChoiceField(RATING_CHOICES)
    usefulness = forms.ChoiceField(RATING_CHOICES)


class AuthorReplyRatingForm(forms.Form):
    clarity = forms.ChoiceField(RATING_CHOICES)
    correctness = forms.ChoiceField(RATING_CHOICES)
    usefulness = forms.ChoiceField(RATING_CHOICES)


class SubmissionRatingForm(forms.Form):
    clarity = forms.ChoiceField(RATING_CHOICES)
    correctness = forms.ChoiceField(RATING_CHOICES)
    usefulness = forms.ChoiceField(RATING_CHOICES)


class ReportRatingForm(forms.Form):
    clarity = forms.ChoiceField(RATING_CHOICES)
    correctness = forms.ChoiceField(RATING_CHOICES)
    usefulness = forms.ChoiceField(RATING_CHOICES)
