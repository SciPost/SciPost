from django import forms 

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
    orcid_id = forms.CharField(label="ORCID id", max_length=20, required=False)
    affiliation = forms.CharField(label='Affiliation', max_length=300)
    address = forms.CharField(label='Address', max_length=1000, required=False)
    personalwebpage = forms.URLField(label='Personal web page', required=False)
    username = forms.CharField(label='username', max_length=100)
    password = forms.CharField(label='password', widget=forms.PasswordInput())
    password_verif = forms.CharField(label='verify pwd', widget=forms.PasswordInput())

class VetRegistrationForm(forms.Form):
    promote_to_rank_1 = forms.BooleanField(required=False)
    refusal_reason = forms.ChoiceField(choices=REGISTRATION_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)

class AuthenticationForm(forms.Form):
    username = forms.CharField(label='username', max_length=100)
    password = forms.CharField(label='password', widget=forms.PasswordInput())


