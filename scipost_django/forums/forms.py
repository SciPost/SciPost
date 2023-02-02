__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django import forms
from django.contrib.auth.models import Group

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Hidden, ButtonHolder, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete

from .models import Forum, Meeting, Post, Motion

from markup.widgets import TextareaWithPreview
from organizations.models import Organization


class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = [
            "name",
            "slug",
            "description",
            "publicly_visible",
            "moderators",
            "parent_content_type",
            "parent_object_id",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent_content_type"].widget = forms.HiddenInput()
        self.fields["parent_object_id"].widget = forms.HiddenInput()


class MeetingForm(ForumForm):
    class Meta:
        model = Meeting
        fields = [
            "name",
            "slug",
            "description",
            "publicly_visible",
            "moderators",
            "parent_content_type",
            "parent_object_id",
            "date_from",
            "date_until",
            "preamble",
        ]


class ForumGroupPermissionsForm(forms.ModelForm):
    """
    Used for granting specific Groups some rights to a given Forum.
    """

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url="/group-autocomplete"),
    )
    can_administer = forms.BooleanField(required=False)
    can_view = forms.BooleanField(required=False)
    can_post = forms.BooleanField(required=False)

    class Meta:
        model = Forum
        fields = []


class ForumOrganizationPermissionsForm(forms.Form):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
    )
    can_view = forms.BooleanField()
    can_post = forms.BooleanField()


class PostForm(forms.ModelForm):
    """
    Create a new Post. The parent must be defined, the model class and
    instance being defined by url parameters.
    """

    class Meta:
        model = Post
        fields = [
            "posted_by",
            "posted_on",
            "needs_vetting",
            "parent_content_type",
            "parent_object_id",
            "subject",
            "text",
        ]

    def __init__(self, *args, **kwargs):
        self.forum = kwargs.pop("forum")
        super().__init__(*args, **kwargs)
        self.fields["text"].widget = TextareaWithPreview()
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("posted_by", type="hidden"),
            Field("posted_on", type="hidden"),
            Field("needs_vetting", type="hidden"),
            Field("parent_content_type", type="hidden"),
            Field("parent_object_id", type="hidden"),
            FloatingField("subject"),
            Field("text"),
            Submit("submit", "Submit"),
        )

    def clean_posted_on(self):
        if self.forum.meeting:
            if datetime.date.today() > self.forum.meeting.date_until:
                self.add_error(
                    "posted_on",
                    "You cannot Post to a Meeting which is finished.",
                )
            elif datetime.date.today() < self.forum.meeting.date_from:
                self.add_error(
                    "posted_on",
                    "This meeting has not started yet, please come back later!",
                )
        return self.cleaned_data["posted_on"]


class MotionForm(PostForm):
    """
    Form for creating a Motion to be voted on in a Forum or during a Meeting.
    """

    class Meta:
        model = Motion
        fields = [
            "posted_by",
            "posted_on",
            "needs_vetting",
            "parent_content_type",
            "parent_object_id",
            "subject",
            "text",
            "eligible_for_voting",
            "voting_deadline",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["eligible_for_voting"].widget = forms.HiddenInput()
        self.fields["eligible_for_voting"].disabled = True
