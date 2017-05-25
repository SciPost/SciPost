import string
import random

from django import forms

from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password

from django_countries import countries
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import LazyTypedChoiceField
from captcha.fields import ReCaptchaField

from ajax_select.fields import AutoCompleteSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, HTML

from .constants import SCIPOST_DISCIPLINES, TITLE_CHOICES, SCIPOST_FROM_ADDRESSES
from .models import Contributor, DraftInvitation, RegistrationInvitation,\
                    UnavailabilityPeriod, PrecookedEmail

from journals.models import Publication
from mailing_lists.models import MailchimpList, MailchimpSubscription


REGISTRATION_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'not a professional scientist (>= PhD student)'),
    (-2, 'another account already exists for this person'),
    (-3, 'barred from SciPost (abusive behaviour)'),
    )
reg_ref_dict = dict(REGISTRATION_REFUSAL_CHOICES)


class RegistrationForm(forms.Form):
    """
    Use this form to process the registration of new accounts.
    Due to the construction of a separate Contributor from the User,
    it is difficult to create a 'combined ModelForm'. All fields
    are thus separately handled here.
    """
    title = forms.ChoiceField(choices=TITLE_CHOICES, label='* Title')
    first_name = forms.CharField(label='* First name', max_length=100)
    last_name = forms.CharField(label='* Last name', max_length=100)
    email = forms.EmailField(label='* Email address')
    invitation_key = forms.CharField(max_length=40, widget=forms.HiddenInput(), required=False)
    orcid_id = forms.CharField(label="ORCID id", max_length=20, required=False,
                               widget=forms.TextInput(
                                    {'placeholder': 'Recommended. Get one at orcid.org'}))
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
    password_verif = forms.CharField(label='* Verify password', widget=forms.PasswordInput())
    captcha = ReCaptchaField(attrs={'theme': 'clean'}, label='*Please verify to continue:')

    def clean_password_verif(self):
        password = self.cleaned_data.get('password', '')
        user = User(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data['email']
        )
        validate_password(password, user)
        # raise
        # return 'piemel'

    # def clean_password_verif(self):
    #     t = self.cleaned_data
        if self.cleaned_data['password'] != self.cleaned_data['password_verif']:
            self.add_error('password', 'Your passwords must match')
            self.add_error('password_verif', 'Your passwords must match')
        return self.cleaned_data.get('password', '')

    def clean_username(self):
        if User.objects.filter(username=self.cleaned_data['username']).exists():
            self.add_error('username', 'This username is already in use')
        return self.cleaned_data.get('username', '')

    def clean_email(self):
        if User.objects.filter(email=self.cleaned_data['email']).exists():
            self.add_error('email', 'This email address is already in use')
        return self.cleaned_data.get('email', '')

    def create_and_save_contributor(self):
        user = User.objects.create_user(**{
            'first_name': self.cleaned_data['first_name'],
            'last_name': self.cleaned_data['last_name'],
            'email': self.cleaned_data['email'],
            'username': self.cleaned_data['username'],
            'password': self.cleaned_data['password'],
            'is_active': False
        })
        contributor, new = Contributor.objects.get_or_create(**{
            'user': user,
            'invitation_key': self.cleaned_data.get('invitation_key', ''),
            'title': self.cleaned_data['title'],
            'orcid_id': self.cleaned_data['orcid_id'],
            'country_of_employment': self.cleaned_data['country_of_employment'],
            'address': self.cleaned_data['address'],
            'affiliation': self.cleaned_data['affiliation'],
            'personalwebpage': self.cleaned_data['personalwebpage'],
        })

        if contributor.activation_key == '':
            # Seems redundant?
            contributor.generate_key()
        contributor.save()
        return contributor


class DraftInvitationForm(forms.ModelForm):
    cited_in_submission = AutoCompleteSelectField('submissions_lookup', required=False)
    cited_in_publication = AutoCompleteSelectField('publication_lookup', required=False)

    class Meta:
        model = DraftInvitation
        fields = ['title', 'first_name', 'last_name', 'email',
                  'invitation_type',
                  'cited_in_submission', 'cited_in_publication'
                  ]


class RegistrationInvitationForm(forms.ModelForm):
    cited_in_submission = AutoCompleteSelectField('submissions_lookup', required=False)
    cited_in_publication = AutoCompleteSelectField('publication_lookup', required=False)

    class Meta:
        model = RegistrationInvitation
        fields = ['title', 'first_name', 'last_name', 'email',
                  'invitation_type',
                  'cited_in_submission', 'cited_in_publication',
                  'message_style', 'personal_message'
                  ]

    def __init__(self, *args, **kwargs):
        if kwargs.get('initial', {}).get('cited_in_submission', False):
            kwargs['initial']['cited_in_submission'] = kwargs['initial']['cited_in_submission'].id
        if kwargs.get('initial', {}).get('cited_in_publication', False):
            kwargs['initial']['cited_in_publication'] = kwargs['initial']['cited_in_publication'].id

        super(RegistrationInvitationForm, self).__init__(*args, **kwargs)
        self.fields['personal_message'].widget.attrs.update(
            {'placeholder': ('NOTE: a personal phrase or two.'
                             ' The bulk of the text will be auto-generated.')})


        self.fields['cited_in_publication'] = forms.ModelChoiceField(
            queryset=Publication.objects.all().order_by('-publication_date'),
            required=False)


class ModifyPersonalMessageForm(forms.Form):
    personal_message = forms.CharField(widget=forms.Textarea())


class UpdateUserDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['last_name'].widget.attrs['readonly'] = True

    def clean_last_name(self):
        '''Make sure the `last_name` cannot be saved via this form.'''
        instance = getattr(self, 'instance', None)
        if instance and instance.last_name:
            return instance.last_name
        else:
            return self.cleaned_data['last_name']


class UpdatePersonalDataForm(forms.ModelForm):
    class Meta:
        model = Contributor
        fields = ['title', 'discipline', 'expertises', 'orcid_id', 'country_of_employment',
                  'affiliation', 'address', 'personalwebpage'
                  ]
        widgets = {'country_of_employment': CountrySelectWidget()}

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['mail_subscription'] = forms.ModelMultipleChoiceField(
    #             queryset=MailchimpList.objects.open_to_subscribe(kwargs['instance']).distinct(),
    #             widget=forms.CheckboxSelectMultiple(),
    #             label='Subscribe to the following mailing lists:',
    #             required=False)
    #     self.fields['mailing_lists'] = forms.ModelMultipleChoiceField(
    #             queryset=MailchimpList.objects.open_to_subscribe(kwargs['instance']).distinct(),
    #             widget=forms.CheckboxSelectMultiple(),
    #             label='Subscribe to the following mailing lists:',
    #             required=False)

    def sync_lists(self):
        return
        # contributor = self.instance
        # original_lists = list(self.fields['mailing_lists'].queryset)
        #
        # # Subscribe to lists
        # for _list in self.cleaned_data['mailing_lists']:
        #     _list.update_membership([contributor])
        #     original_lists.remove(_list)
        #
        # # Unsubscribe from the leftovers
        # for _list in original_lists:
        #     _list.update_membership([contributor], status='unsubscribed')


class VetRegistrationForm(forms.Form):
    decision = forms.ChoiceField(widget=forms.RadioSelect,
                                 choices=((True, 'Accept registration'), (False, 'Refuse')))
    refusal_reason = forms.ChoiceField(choices=REGISTRATION_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(),
                                           label='Justification (optional)', required=False)

    def promote_to_registered_contributor(self):
        return self.cleaned_data.get('decision') == 'True'


class AuthenticationForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput())


class PasswordChangeForm(forms.Form):
    password_prev = forms.CharField(label='Existing password', widget=forms.PasswordInput())
    password_new = forms.CharField(label='New password', widget=forms.PasswordInput())
    password_verif = forms.CharField(label='Reenter new password', widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

    def clean_password_new(self):
        password = self.cleaned_data['password_new']
        validate_password(password, self.current_user)
        return password


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
    q = forms.CharField(max_length=100)


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
