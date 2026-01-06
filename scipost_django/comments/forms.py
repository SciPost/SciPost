__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.db.models import Q, QuerySet

from crispy_forms.layout import Layout, Div
from crispy_bootstrap5.bootstrap5 import FloatingField

from common.forms import CrispyFormMixin, SearchForm

from .constants import (
    COMMENT_ACTION_CHOICES,
    COMMENT_ACTION_REFUSE,
    COMMENT_REFUSAL_CHOICES,
    COMMENT_REFUSAL_EMPTY,
)
from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = [
            "is_cor",
            "is_rem",
            "is_que",
            "is_ans",
            "is_obj",
            "is_rep",
            "is_val",
            "is_lit",
            "is_sug",
            "comment_text",
            "remarks_for_editors",
            "file_attachment",
            "anonymous",
        ]

    def __init__(self, *args, **kwargs):
        self.is_report_comment = kwargs.pop("is_report_comment", False)
        super().__init__(*args, **kwargs)
        self.fields["comment_text"].widget.attrs.update(
            {
                "placeholder": "NOTE: only serious and meaningful Comments will be accepted."
            }
        )
        self.fields["remarks_for_editors"].widget.attrs.update(
            {"rows": 3, "placeholder": "(these remarks will not be publicly visible)"}
        )
        self.fields["anonymous"].initial = True

        if self.is_report_comment:
            del self.fields["anonymous"]


class VetCommentForm(forms.Form):
    action_option = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=COMMENT_ACTION_CHOICES,
        required=True,
        label="Action",
    )
    refusal_reason = forms.ChoiceField(choices=COMMENT_REFUSAL_CHOICES)
    email_response_field = forms.CharField(
        widget=forms.Textarea(), label="Justification (optional)", required=False
    )

    def clean(self):
        """
        If the comment is refused, make sure a valid refusal reason is given.
        """
        data = super().clean()
        if data["action_option"] == str(COMMENT_ACTION_REFUSE):
            if data["refusal_reason"] == str(COMMENT_REFUSAL_EMPTY):
                self.add_error(None, "Please choose a valid refusal reason")
        return data


class CommentTextSearchForm(forms.Form):
    """Search for Comment"""

    text = forms.CharField(max_length=1000, required=False, label="Text")

    def search_results(self):
        """Return all Comment objects according to search"""
        return (
            Comment.objects.vetted()
            .filter(
                comment_text__icontains=self.cleaned_data["text"],
            )
            .order_by("-date_submitted")
        )


class CommentSearchForm(CrispyFormMixin, SearchForm[Comment]):
    model = Comment
    queryset = Comment.objects.vetted()

    object_title = forms.CharField(max_length=100, required=False)

    def __init__(self, *args, **kwargs):
        self.acad_field_slug = kwargs.pop("acad_field_slug")
        self.specialty_slug = kwargs.pop("specialty_slug")
        super().__init__(*args, **kwargs)

    def get_form_layout(self) -> Layout:
        return Layout(Div(Div(FloatingField("object_title"), css_class="col")))

    def filter_queryset(self, queryset: "QuerySet[Comment]"):
        if self.acad_field_slug and self.acad_field_slug != "all":
            queryset = queryset.filter(
                Q(submissions__acad_field__slug=self.acad_field_slug)
                | Q(reports__submission__acad_field__slug=self.acad_field_slug)
                | Q(commentaries__acad_field__slug=self.acad_field_slug)
            )
        if self.specialty_slug and self.specialty_slug != "all":
            queryset = queryset.filter(
                Q(submissions__specialties__slug=self.specialty_slug)
                | Q(reports__submission__specialties__slug=self.specialty_slug)
                | Q(commentaries__specialties__slug=self.specialty_slug)
            )
        if title := self.cleaned_data.get("object_title"):
            queryset = queryset.filter(
                Q(submissions__title__icontains=title)
                | Q(reports__submission__title__icontains=title)
                | Q(commentaries__title__icontains=title)
            )
        return queryset.distinct()
