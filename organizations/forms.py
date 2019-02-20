__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django import forms

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .constants import ROLE_GENERAL
from .models import Contact, ContactRole

from scipost.constants import TITLE_CHOICES


class ContactForm(forms.ModelForm):
    """
    This Contact form is mainly used for editing Contact instances.
    """
    class Meta:
        model = Contact
        fields = ['title', 'key_expires']


class NewContactForm(ContactForm):
    """
    This Contact form is used to create new Contact instances, as it will also handle
    possible sending and activation of User instances coming with the new Contact.
    """
    title = forms.ChoiceField(choices=TITLE_CHOICES, label='Title')
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.CharField()
    existing_user = None

    def __init__(self, *args, **kwargs):
        """
        Organization is a required argument to tell the formset which Organization
        the Contact is being edited for in the current form.
        """
        self.organization = kwargs.pop('organization')
        super().__init__(*args, **kwargs)

    def clean_email(self):
        """
        Check if User already is known in the system.
        """
        email = self.cleaned_data['email']
        try:
            self.existing_user = User.objects.get(email=email)
            if not self.data.get('confirm_use_existing', '') == 'on':
                # Do not give error if user wants to use existing User
                self.add_error('email', 'This User is already registered.')
            self.fields['confirm_use_existing'] = forms.BooleanField(
                required=False, initial=False, label='Use the existing user instead: %s %s'
                                                     % (self.existing_user.first_name,
                                                        self.existing_user.last_name))
        except User.DoesNotExist:
            pass
        return email

    @transaction.atomic
    def save(self, current_user, commit=True):
        """
        If existing user is found, link it to the Organization.
        """
        if self.existing_user and self.data.get('confirm_use_existing', '') == 'on':
            # Create new Contact if it doesn't already exist
            try:
                # Link Contact to new Organization
                contact = self.existing_user.org_contact
            except Contact.DoesNotExist:
                # Not yet a 'Contact-User'
                contact = super().save(commit=False)
                contact.title = self.existing_user.org_contact.title
                contact.user = self.existing_user
                contact.save()
            return contact

        # Create complete new Account (User + Contact)
        user = User(
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data['email'],
            username=self.cleaned_data['email'],
            is_active=False,
        )
        user.save()
        contact = Contact(
            user=user,
            title=self.cleaned_data['title']
        )
        contact.generate_key()
        contact.save()

        # Create the role with to-be-updated info
        contactrole = ContactRole(
            contact=contact,
            organization=self.organization,
            kind=[ROLE_GENERAL,],
            date_from=timezone.now(),
            date_until=timezone.now() + datetime.timedelta(days=3650)
        )
        contactrole.save()

        return contact


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


class ContactRoleForm(forms.ModelForm):

    class Meta:
        model = ContactRole
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['organization'].disabled = True
            self.fields['contact'].disabled = True
