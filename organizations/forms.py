__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from .constants import ROLE_KINDS
from .models import Contact


class ContactActivationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = []

    password_new = forms.CharField(label='* Password', widget=forms.PasswordInput())
    password_verif = forms.CharField(label='* Verify password', widget=forms.PasswordInput(),
                                     help_text='Your password must contain at least 8 characters')

    def clean(self, *args, **kwargs):
        try:
            self.instance.org_contact
        except Contact.DoesNotExist:
            self.add_error(None, 'Your account is invalid, please contact the administrator.')
        return super().clean(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password_new', '')
        try:
            validate_password(password, self.instance)
        except ValidationError as error_message:
            self.add_error('password_new', error_message)
        return password

    def clean_password_verif(self):
        if self.cleaned_data.get('password_new', '') != self.cleaned_data.get('password_verif', ''):
            self.add_error('password_verif', 'Your password entries must match')
        return self.cleaned_data.get('password_verif', '')

    @transaction.atomic
    def activate_user(self):
        if self.errors:
            return forms.ValidationError

        # Activate account
        self.instance.is_active = True
        self.instance.set_password(self.cleaned_data['password_new'])
        self.instance.save()

        return self.instance
