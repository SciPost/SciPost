__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from ajax_select.fields import AutoCompleteSelectField

from .models import Forum, Meeting, Post, Motion


class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['name', 'slug', 'description',
                  'publicly_visible', 'moderators',
                  'parent_content_type', 'parent_object_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_content_type'].widget = forms.HiddenInput()
        self.fields['parent_object_id'].widget = forms.HiddenInput()


class MeetingForm(ForumForm):
    class Meta:
        model = Meeting
        fields = ['name', 'slug', 'description',
                  'publicly_visible', 'moderators',
                  'parent_content_type', 'parent_object_id',
                  'date_from', 'date_until', 'preamble']


class ForumGroupPermissionsForm(forms.ModelForm):
    """
    Used for granting a specific Group access to a given Forum.
    """
    group = AutoCompleteSelectField('group_lookup')
    can_view = forms.BooleanField(required=False)
    can_post = forms.BooleanField(required=False)

    class Meta:
        model = Forum
        fields = []


class ForumOrganizationPermissionsForm(forms.Form):
    organization = AutoCompleteSelectField('organization_lookup')
    can_view = forms.BooleanField()
    can_post = forms.BooleanField()


class PostForm(forms.ModelForm):
    """
    Create a new Post. The parent must be defined, the model class and
    instance being defined by url parameters.
    """
    class Meta:
        model = Post
        fields = ['posted_by', 'posted_on', 'needs_vetting',
                  'parent_content_type', 'parent_object_id',
                  'subject', 'text']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['posted_by'].widget = forms.HiddenInput()
        self.fields['posted_on'].widget = forms.HiddenInput()
        self.fields['needs_vetting'].widget = forms.HiddenInput()
        self.fields['parent_content_type'].widget = forms.HiddenInput()
        self.fields['parent_object_id'].widget = forms.HiddenInput()


class MotionForm(PostForm):
    """
    Form for creating a Motion to be voted on in a Forum or during a Meeting.
    """
    class Meta:
        model = Motion
        fields = ['posted_by', 'posted_on', 'needs_vetting',
                  'parent_content_type', 'parent_object_id',
                  'subject', 'text',
                  'eligible_for_voting', 'voting_deadline']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eligible_for_voting'].widget = forms.HiddenInput()
        self.fields['eligible_for_voting'].disabled = True
