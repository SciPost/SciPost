from django import forms 

from django_countries import countries
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import LazyTypedChoiceField

from .models import *



REGISTRATION_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'not a professional scientist (>= PhD student)'),
    (-2, 'another account already exists for this person'),
    (-3, 'barred from SciPost (abusive behaviour)'),
    )

class RegistrationForm(forms.Form):
    title = forms.ChoiceField(choices=TITLE_CHOICES)
    first_name = forms.CharField(label='First name', max_length=100)
    last_name = forms.CharField(label='Last name', max_length=100)
    email = forms.EmailField(label='email')
    orcid_id = forms.CharField(label="ORCID id", max_length=20)
    nationality = LazyTypedChoiceField(choices=countries, initial='CA', widget=CountrySelectWidget(layout='{widget}<img class="country-select-flag" id="{flag_id}" style="margin: 6px 4px 0" src="{country.flag}">'))
    country_of_employment = LazyTypedChoiceField(choices=countries, initial='NL', widget=CountrySelectWidget(layout='{widget}<img class="country-select-flag" id="{flag_id}" style="margin: 6px 4px 0" src="{country.flag}">'))
    affiliation = forms.CharField(label='Affiliation', max_length=300)
    #address = forms.CharField(label='Address', max_length=1000)
    personalwebpage = forms.URLField(label='Personal web page')
    username = forms.CharField(label='username', max_length=100)
    password = forms.CharField(label='password', widget=forms.PasswordInput())
    password_verif = forms.CharField(label='verify pwd', widget=forms.PasswordInput())

#class RegistrationFormUser(forms.ModelForm):
#    class Meta:
#        model = User
#        fields = ['email', 'first_name', 'last_name']

#class RegistrationFormContributor(forms.ModelForm):
#    class Meta:
#        model = Contributor
#        fields = ['title', 'orcid_id', 'affiliation', 'address', 'personalwebpage']


#class UpdatePersonalDataForm(forms.Form):
#    title = forms.ChoiceField(choices=TITLE_CHOICES)
#    first_name = forms.CharField(label='First name', max_length=100)
#    last_name = forms.CharField(label='Last name', max_length=100)
#    email = forms.EmailField(label='email')
#    orcid_id = forms.CharField(label="ORCID id", max_length=20, required=False)
#    affiliation = forms.CharField(label='Affiliation', max_length=300)
#    address = forms.CharField(label='Address', max_length=1000, required=False)
#    personalwebpage = forms.URLField(label='Personal web page', required=False)

# Replace this by the following two ModelForms:
class UpdateUserDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

class UpdatePersonalDataForm(forms.ModelForm):
    class Meta:
        model = Contributor
        #fields = ['title', 'first_name', 'last_name', 'email', 'orcid_id', 'affiliation', 'address', 'personalwebpage']
        #fields = ['title', 'orcid_id', 'affiliation', 'address', 'personalwebpage']
        #fields = ['title', 'orcid_id', 'affiliation', 'personalwebpage']
        fields = ['title', 'orcid_id', 'nationality', 'country_of_employment', 'affiliation', 'personalwebpage']
        widgets = {'nationality': CountrySelectWidget(layout='{widget}<img class="country-select-flag" id="{flag_id}" style="margin: 6px 4px 0" src="{country.flag}">'), 'country_of_employment': CountrySelectWidget()}

class VetRegistrationForm(forms.Form):
    promote_to_rank_1 = forms.BooleanField(required=False)
    refusal_reason = forms.ChoiceField(choices=REGISTRATION_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)

class AuthenticationForm(forms.Form):
    username = forms.CharField(label='username', max_length=100)
    password = forms.CharField(label='password', widget=forms.PasswordInput())

class PasswordChangeForm(forms.Form):
    password_prev = forms.CharField(label='Existing password', widget=forms.PasswordInput())
    password_new = forms.CharField(label='New password', widget=forms.PasswordInput())
    password_verif = forms.CharField(label='Reenter new password', widget=forms.PasswordInput())

