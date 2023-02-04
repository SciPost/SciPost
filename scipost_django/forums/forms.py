__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django import forms
from django.contrib.auth.models import User, Group
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Hidden, ButtonHolder, Submit
from crispy_forms.bootstrap import FieldWithButtons, StrictButton, InlineRadios
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
    parent = forms.ModelChoiceField(queryset=Forum.objects.anchors())

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
            "parent",
            "date_from",
            "date_until",
            "preamble",
            "minutes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["parent"].initial = self.instance.parent

    def save(self):
        meeting = super().save()
        meeting.parent = self.cleaned_data["parent"]
        meeting.save()
        return meeting


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
                    None, # if set to "posted_on", does not show: field is hidden
                    "You cannot Post to a Meeting which is finished.",
                )
            elif datetime.date.today() < self.forum.meeting.date_from:
                self.add_error(
                    None, # see comment above
                    "This meeting has not started yet, please come back later!",
                )
        return timezone.now()


class MotionForm(PostForm):
    """
    Form for creating a Motion to be voted on in a Forum or during a Meeting.
    """

    class Meta:
        model = Motion
        fields = [
            "posted_by",
            "posted_on",
            "parent_content_type",
            "parent_object_id",
            "subject",
            "text",
            "eligible_for_voting",
            "voting_deadline",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Field("posted_by", type="hidden"),
            Field("posted_on", type="hidden"),
            Field("parent_content_type", type="hidden"),
            Field("parent_object_id", type="hidden"),
            FloatingField("subject"),
            Field("text"),
            Field("eligible_for_voting", type="hidden"),
            Field("voting_deadline", type="hidden"),
            Submit("submit", "Submit"),
        )


class MotionVoteForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    motion = forms.ModelChoiceField(queryset=Motion.objects.all())
    vote = forms.ChoiceField(
        choices=(
            ("Y", "Agree"),
            ("M", "Doubt"),
            ("N", "Disagree"),
            ("A", "Abstain"),
        ),
    )

    def clean_motion(self):
        if datetime.date.today() > self.cleaned_data["motion"].voting_deadline:
            self.add_error("motion", "Motion is not open for voting anymore")
            return None
        return self.cleaned_data["motion"]

    def clean_vote(self):
        if self.cleaned_data["vote"] not in ["Y", "M", "N", "A"]:
            self.add_error("vote", "Invalid vote")
        return self.cleaned_data["vote"]

    def clean(self):
        self.cleaned_data = super().clean()
        if (
                hasattr(self.cleaned_data, "user") and
                hasattr(self.cleaned_data, "motion") and
                (
                    self.cleaned_data["user"] not in
                    self.cleaned_data["motion"].eligible_for_voting.all()
                )
            ):
            self.add_error("", "Not eligible to vote on this Motion")
        return self.cleaned_data

    def save(self):
        user = self.cleaned_data["user"]
        motion = self.cleaned_data["motion"]
        vote = self.cleaned_data["vote"]
        motion.in_agreement.remove(user)
        motion.in_doubt.remove(user)
        motion.in_disagreement.remove(user)
        motion.in_abstain.remove(user)
        if vote == "Y":
            motion.in_agreement.add(user)
        elif vote == "M":
            motion.in_doubt.add(user)
        elif vote == "N":
            motion.in_disagreement.add(user)
        elif vote == "A":
            motion.in_abstain.add(user)
        motion.save()
