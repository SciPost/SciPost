from django import forms

from .models import *


class PublicationTypeRatingForm(forms.Form):
    """ Abstract base class for all publication-type rating forms. """
    clarity = forms.ChoiceField(RATING_CHOICES)
    validity = forms.ChoiceField(RATING_CHOICES)
    rigour = forms.ChoiceField(RATING_CHOICES)
    originality = forms.ChoiceField(RATING_CHOICES)
    significance = forms.ChoiceField(RATING_CHOICES)

    class Meta:
        abstract = True

class CommentTypeRatingForm(forms.Form):
    """ Abstract base class for all comment-type rating forms. """
    relevance = forms.ChoiceField(RATING_CHOICES)
    importance = forms.ChoiceField(RATING_CHOICES)
    clarity = forms.ChoiceField(RATING_CHOICES)
    validity = forms.ChoiceField(RATING_CHOICES)
    rigour = forms.ChoiceField(RATING_CHOICES)

    class Meta:
        abstract = True


class CommentaryRatingForm(PublicationTypeRatingForm):
    pass

class CommentRatingForm(CommentTypeRatingForm):
    pass

class AuthorReplyRatingForm(CommentTypeRatingForm):
    pass

class SubmissionRatingForm(PublicationTypeRatingForm):
    pass

class ReportRatingForm(CommentTypeRatingForm):
    pass
