from django import forms

from django.contrib.auth.models import User, Group
from django.db.models import Q

from django_countries import countries
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import LazyTypedChoiceField
from captcha.fields import ReCaptchaField

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, HTML, Submit

from .constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from .models import TITLE_CHOICES, SCIPOST_FROM_ADDRESSES, ARC_LENGTHS,\
                     Contributor, DraftInvitation, RegistrationInvitation,\
                     SupportingPartner, SPBMembershipAgreement,\
                     UnavailabilityPeriod, PrecookedEmail,\
                     List, Team, Graph, Node
from virtualmeetings.models import Feedback, Nomination, Motion

from journals.models import Publication
from submissions.models import SUBMISSION_STATUS_PUBLICLY_UNLISTED
from submissions.models import Submission


REGISTRATION_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'not a professional scientist (>= PhD student)'),
    (-2, 'another account already exists for this person'),
    (-3, 'barred from SciPost (abusive behaviour)'),
    )
reg_ref_dict = dict(REGISTRATION_REFUSAL_CHOICES)


class RegistrationForm(forms.Form):
    title = forms.ChoiceField(choices=TITLE_CHOICES, label='* Title')
    first_name = forms.CharField(label='* First name', max_length=100)
    last_name = forms.CharField(label='* Last name', max_length=100)
    email = forms.EmailField(label='* Email address')
    orcid_id = forms.CharField(
        label="  ORCID id", max_length=20,
        widget=forms.TextInput({'placeholder': 'Recommended. Get one at orcid.org'}),
        required=False)
    discipline = forms.ChoiceField(choices=SCIPOST_DISCIPLINES, label='* Main discipline')
    country_of_employment = LazyTypedChoiceField(
        choices=countries, label='* Country of employment', initial='NL',
        widget=CountrySelectWidget(layout=(
            '{widget}<img class="country-select-flag" id="{flag_id}"'
            ' style="margin: 6px 4px 0" src="{country.flag}">')))
    affiliation = forms.CharField(label='* Affiliation', max_length=300)
    address = forms.CharField(
        label='Address', max_length=1000,
        widget=forms.TextInput({'placeholder': 'For postal correspondence'}),
        required=False)
    personalwebpage = forms.URLField(
        label='Personal web page',
        widget=forms.TextInput({'placeholder': 'full URL, e.g. http://www.[yourpage].com'}),
        required=False)
    username = forms.CharField(label='* Username', max_length=100)
    password = forms.CharField(label='* Password', widget=forms.PasswordInput())
    password_verif = forms.CharField(label='* Verify pwd', widget=forms.PasswordInput())
    captcha = ReCaptchaField(attrs={
  'theme' : 'clean',
}, label='* Answer this simple maths question:')


class DraftInvitationForm(forms.ModelForm):
    class Meta:
        model = DraftInvitation
        fields = ['title', 'first_name', 'last_name', 'email',
                  'invitation_type',
                  'cited_in_submission', 'cited_in_publication'
                  ]

    def __init__(self, *args, **kwargs):
        super(DraftInvitationForm, self).__init__(*args, **kwargs)
        self.fields['cited_in_submission'] = forms.ModelChoiceField(
            queryset=Submission.objects.all().exclude(
                status__in=SUBMISSION_STATUS_PUBLICLY_UNLISTED).order_by('-submission_date'),
            required=False)
        self.fields['cited_in_publication'] = forms.ModelChoiceField(
            queryset=Publication.objects.all().order_by('-publication_date'),
            required=False)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('title'), Field('first_name'), Field('last_name'),
                    Field('email'), Field('invitation_type'),
                    css_class="col-6"),
                Div(
                    Submit('submit', 'Save draft'),
                    css_class="col-6"),
                css_class="row"),
            Div(Field('cited_in_submission'),),
            Div(Field('cited_in_publication'),),
            )


class RegistrationInvitationForm(forms.ModelForm):
    class Meta:
        model = RegistrationInvitation
        fields = ['title', 'first_name', 'last_name', 'email',
                  'invitation_type',
                  'cited_in_submission', 'cited_in_publication',
                  'message_style', 'personal_message'
                  ]

    def __init__(self, *args, **kwargs):
        super(RegistrationInvitationForm, self).__init__(*args, **kwargs)
        self.fields['personal_message'].widget.attrs.update(
            {'placeholder': ('NOTE: a personal phrase or two.'
                             ' The bulk of the text will be auto-generated.')})
        self.fields['cited_in_submission'] = forms.ModelChoiceField(
            queryset=Submission.objects.all().exclude(
                status__in=SUBMISSION_STATUS_PUBLICLY_UNLISTED).order_by('-submission_date'),
            required=False)
        self.fields['cited_in_publication'] = forms.ModelChoiceField(
            queryset=Publication.objects.all().order_by('-publication_date'),
            required=False)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('title'), Field('first_name'), Field('last_name'),
                    Field('email'), Field('invitation_type'),
                    css_class="col-6"),
                Div(
                    Field('message_style'),
                    Field('personal_message'),
                    Submit('submit', 'Send invitation'),
                    css_class="col-6"),
                css_class="row"),
            Div(Field('cited_in_submission'),),
            Div(Field('cited_in_publication'),),
            )


class ModifyPersonalMessageForm(forms.Form):
    personal_message = forms.CharField(widget=forms.Textarea())


class UpdateUserDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']


class UpdatePersonalDataForm(forms.ModelForm):
    class Meta:
        model = Contributor
        fields = ['title', 'discipline', 'expertises', 'orcid_id', 'country_of_employment',
                  'affiliation', 'address', 'personalwebpage',
                  'accepts_SciPost_emails'
                  ]
        widgets = {'country_of_employment': CountrySelectWidget()}


class VetRegistrationForm(forms.Form):
    promote_to_registered_contributor = forms.BooleanField(required=False,
                                                           label='Accept registration')
    refuse = forms.BooleanField(required=False)
    refusal_reason = forms.ChoiceField(choices=REGISTRATION_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(),
                                           label='Justification (optional)', required=False)


class AuthenticationForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput())


class PasswordChangeForm(forms.Form):
    password_prev = forms.CharField(label='Existing password', widget=forms.PasswordInput())
    password_new = forms.CharField(label='New password', widget=forms.PasswordInput())
    password_verif = forms.CharField(label='Reenter new password', widget=forms.PasswordInput())


AUTHORSHIP_CLAIM_CHOICES = (
    ('-', '-'),
    ('True', 'I am an author'),
    ('False', 'I am not an author'),
    )


class AuthorshipClaimForm(forms.Form):
    claim = forms.ChoiceField(choices=AUTHORSHIP_CLAIM_CHOICES, required=False)


class UnavailabilityPeriodForm(forms.ModelForm):
    class Meta:
        model = UnavailabilityPeriod
        fields = ['start', 'end']

    def __init__(self, *args, **kwargs):
        super(UnavailabilityPeriodForm, self).__init__(*args, **kwargs)
        self.fields['start'].widget.attrs.update({'placeholder': 'YYYY-MM-DD'})
        self.fields['end'].widget.attrs.update({'placeholder': 'YYYY-MM-DD'})


class RemarkForm(forms.Form):
    remark = forms.CharField(widget=forms.Textarea(), label='')

    def __init__(self, *args, **kwargs):
        super(RemarkForm, self).__init__(*args, **kwargs)
        self.fields['remark'].widget.attrs.update(
            {'rows': 3, 'cols': 40,
             'placeholder': 'Enter your remarks here. You can use LaTeX in $...$ or \[ \].'})


class SearchForm(forms.Form):
    q = forms.CharField(max_length=100, label='', widget=forms.TextInput(attrs={
                        'class': 'form-control mr-0 mb-2 mr-lg-2 mb-lg-0'}))


class EmailGroupMembersForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.all())
    email_subject = forms.CharField(widget=forms.Textarea(), label='')
    personalize = forms.BooleanField(
        required=False, initial=False,
        label='Personalize (Dear Prof. AAA)?')
    email_text = forms.CharField(widget=forms.Textarea(), label='')
    include_scipost_summary = forms.BooleanField(
        required=False, initial=False,
        label='include SciPost summary at end of message')

    def __init__(self, *args, **kwargs):
        super(EmailGroupMembersForm, self).__init__(*args, **kwargs)
        self.fields['email_subject'].widget.attrs.update(
            {'rows': 1, 'cols': 50, 'placeholder': 'Email subject'})
        self.fields['email_text'].widget.attrs.update(
            {'rows': 15, 'cols': 50, 'placeholder': 'Write your message in this box.'})


class EmailParticularForm(forms.Form):
    email_address = forms.EmailField(label='')
    email_subject = forms.CharField(widget=forms.Textarea(), label='')
    email_text = forms.CharField(widget=forms.Textarea(), label='')
    include_scipost_summary = forms.BooleanField(
        required=False, initial=False,
        label='Include SciPost summary at end of message')

    def __init__(self, *args, **kwargs):
        super(EmailParticularForm, self).__init__(*args, **kwargs)
        self.fields['email_address'].widget.attrs.update(
            {'placeholder': 'Email address'})
        self.fields['email_subject'].widget.attrs.update(
            {'rows': 1, 'cols': 50, 'placeholder': 'Email subject'})
        self.fields['email_text'].widget.attrs.update(
            {'rows': 15, 'cols': 50, 'placeholder': 'Write your message in this box.'})


class SendPrecookedEmailForm(forms.Form):
    email_address = forms.EmailField()
    email_option = forms.ModelChoiceField(
        queryset=PrecookedEmail.objects.filter(deprecated=False))
    include_scipost_summary = forms.BooleanField(
        required=False, initial=False,
        label='Include SciPost summary at end of message')
    from_address = forms.ChoiceField(choices=SCIPOST_FROM_ADDRESSES)


class CreateListForm(forms.ModelForm):
    class Meta:
        model = List
        fields = ['title', 'description', 'private']

    def __init__(self, *args, **kwargs):
        super(CreateListForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update(
            {'size': 30, 'placeholder': 'Descriptive title for the new List'})
        self.fields['private'].widget.attrs.update({'placeholder': 'Private?'})


class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(CreateTeamForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update(
            {'size': 30, 'placeholder': 'Descriptive name for the new Team'})


class AddTeamMemberForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(AddTeamMemberForm, self).__init__(*args, **kwargs)
        self.fields['last_name'].widget.attrs.update(
            {'size': 20, 'placeholder': 'Search in contributors database'})

    last_name = forms.CharField()


class CreateGraphForm(forms.ModelForm):
    class Meta:
        model = Graph
        fields = ['title', 'description', 'private']

    def __init__(self, *args, **kwargs):
        super(CreateGraphForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update(
            {'size': 30, 'placeholder': 'Descriptive title for the new Graph'})
        self.fields['description'].widget.attrs.update({'placeholder': 'Detailed description'})


class ManageTeamsForm(forms.Form):
    teams_with_access = forms.ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        contributor = kwargs.pop('contributor')
        super(ManageTeamsForm, self).__init__(*args, **kwargs)
        self.fields['teams_with_access'].queryset = Team.objects.filter(
            Q(leader=contributor) | Q(members__in=[contributor]))
        self.fields['teams_with_access'].widget.attrs.update(
            {'placeholder': 'Team(s) to be given access rights:'})


class CreateNodeForm(forms.ModelForm):
    class Meta:
        model = Node
        fields = ['name', 'description']


class CreateArcForm(forms.Form):
    source = forms.ModelChoiceField(queryset=None)
    target = forms.ModelChoiceField(queryset=None)
    length = forms.ChoiceField(choices=ARC_LENGTHS)

    def __init__(self, *args, **kwargs):
        graph = kwargs.pop('graph')
        super(CreateArcForm, self).__init__(*args, **kwargs)
        self.fields['source'].queryset = Node.objects.filter(graph=graph)
        self.fields['target'].queryset = Node.objects.filter(graph=graph)


#############################
# Supporting Partners Board #
#############################

class SupportingPartnerForm(forms.ModelForm):
    class Meta:
        model = SupportingPartner
        fields = ['partner_type', 'institution',
                  'institution_acronym', 'institution_address',
                  'consortium_members'
                  ]

    def __init__(self, *args, **kwargs):
        super(SupportingPartnerForm, self).__init__(*args, **kwargs)
        self.fields['institution_address'].widget = forms.Textarea({'rows': 8, })
        self.fields['consortium_members'].widget.attrs.update(
            {'placeholder': 'Please list the names of the institutions within the consortium', })
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('institution'),
                    Field('institution_acronym'),
                    Field('institution_address'),
                    css_class='col-6'),
                Div(
                    Field('partner_type'),
                    Field('consortium_members'),
                    css_class='col-6'),
                css_class='row')
        )


class SPBMembershipForm(forms.ModelForm):
    class Meta:
        model = SPBMembershipAgreement
        fields = ['start_date', 'duration', 'offered_yearly_contribution']

    def __init__(self, *args, **kwargs):
        super(SPBMembershipForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget.attrs.update({'placeholder': 'YYYY-MM-DD'})
        self.fields['offered_yearly_contribution'].initial = 1000
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('start_date'),
                    css_class="col-4"),
                Div(
                    Field('duration'),
                    css_class="col-2"),
                Div(
                    Field('offered_yearly_contribution'),
                    HTML('(euros)'),
                    css_class="col-4"),
                css_class="row"),
        )


#################
# VGMs, Motions #
#################

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
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('category'),
            Div(
                Div(HTML('<p>Background:</p>'),
                    css_class="col-2"),
                Div(
                    Field('background'),
                    css_class="col-10"),
                css_class="row"),
            Div(
                Div(HTML('<p>Motion:</p>'),
                    css_class="col-2"),
                Div(
                    Field('motion'),
                    css_class="col-10"),
                css_class="row"),
            Submit('submit', 'Submit'),
        )
