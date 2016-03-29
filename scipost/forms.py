from django import forms 

from django_countries import countries
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import LazyTypedChoiceField
from captcha.fields import CaptchaField

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML, Submit

from .models import *



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
    orcid_id = forms.CharField(label="  ORCID id", max_length=20, widget=forms.TextInput({'placeholder': 'Recommended. Get one at orcid.org'}), required=False)
    discipline = forms.ChoiceField(choices=SCIPOST_DISCIPLINES, label='* Main discipline')
    country_of_employment = LazyTypedChoiceField(choices=countries, label='* Country of employment', initial='NL', widget=CountrySelectWidget(layout='{widget}<img class="country-select-flag" id="{flag_id}" style="margin: 6px 4px 0" src="{country.flag}">'))
    affiliation = forms.CharField(label='* Affiliation', max_length=300)
    address = forms.CharField(label='Address', max_length=1000, widget=forms.TextInput({'placeholder': 'For postal correspondence'}), required=False)
    personalwebpage = forms.URLField(label='Personal web page', widget=forms.TextInput({'placeholder': 'full URL, e.g. http://www.[yourpage].com'}), required=False)
    username = forms.CharField(label='* Username', max_length=100)
    password = forms.CharField(label='* Password', widget=forms.PasswordInput())
    password_verif = forms.CharField(label='* Verify pwd', widget=forms.PasswordInput())
    captcha = CaptchaField(label='* I am not a robot')
    invited = forms.BooleanField(widget=forms.HiddenInput())

class RegistrationInvitationForm(forms.ModelForm):
    class Meta:
        model = RegistrationInvitation
        fields = ['title', 'first_name', 'last_name', 'email_address', 'invitation_type', 'message_style', 'personal_message']

    def __init__(self, *args, **kwargs):
        super(RegistrationInvitationForm, self).__init__(*args, **kwargs)
        self.fields['personal_message'].widget.attrs.update({'placeholder': 'NOTE: a personal phrase or two. The bulk of the text will be auto-generated.'})
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('title'), Field('first_name'), Field('last_name'), Field('email_address'), Field('invitation_type'),
                    css_class="col-6"),
                Div(
                    Field('message_style'),
                    Field('personal_message'), 
                    Submit('submit', 'Send invitation'),
                    css_class="col-6"),
                css_class="row"),
            )

class UpdateUserDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

class UpdatePersonalDataForm(forms.ModelForm):
    class Meta:
        model = Contributor
        fields = ['title', 'discipline', 'orcid_id', 'country_of_employment', 'affiliation', 'address', 'personalwebpage']
        widgets = {'country_of_employment': CountrySelectWidget()}

class VetRegistrationForm(forms.Form):
    promote_to_registered_contributor = forms.BooleanField(required=False, label='Accept registration')
    refuse = forms.BooleanField(required=False)
    refusal_reason = forms.ChoiceField(choices=REGISTRATION_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)

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

#class OpinionForm(forms.Form):
#    opinion = forms.ChoiceField(choices=OPINION_CHOICES, label='Your opinion on this Comment: ')


#class AssessmentForm(forms.ModelForm):
#    class Meta:
#        model = Assessment
#        fields = ['relevance', 'importance', 'clarity', 'validity', 'rigour', 'originality', 'significance']
