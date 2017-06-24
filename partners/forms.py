from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q

from captcha.fields import ReCaptchaField
from django_countries import countries
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import LazyTypedChoiceField

from .constants import PARTNER_KINDS, PROSPECTIVE_PARTNER_PROCESSED, CONTACT_TYPES
from .models import Partner, ProspectivePartner, ProspectiveContact, ProspectivePartnerEvent,\
                    Institution, Contact

from scipost.models import TITLE_CHOICES


class ActivationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = []

    password_new = forms.CharField(label='* Password', widget=forms.PasswordInput())
    password_verif = forms.CharField(label='* Verify password', widget=forms.PasswordInput(),
                                     help_text='Your password must contain at least 8 characters')

    def clean(self, *args, **kwargs):
        try:
            self.instance.partner_contact
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

    def activate_user(self):
        if self.errors:
            return forms.ValidationError
        self.instance.is_active = True
        self.instance.set_password(self.cleaned_data['password_new'])
        self.instance.save()
        group = Group.objects.get(name='Partners Accounts')
        self.instance.groups.add(group)
        return self.instance


class InstitutionForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = (
            'kind',
            'name',
            'acronym',
            'address',
            'country'
        )


class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = (
            'institution',
            'status',
            'main_contact'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['main_contact'].queryset = self.instance.contact_set.all()


class ContactForm(forms.ModelForm):
    """
    This Contact form is mainly used for editing Contact instances.
    """
    class Meta:
        model = Contact
        fields = (
            'kind',
        )


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
        Partner is a required argument to tell the formset which Partner the Contact
        is being edited for in the current form.
        """
        self.partner = kwargs.pop('partner')
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

    def save(self, commit=True):
        """
        If existing user is found, add it to the Partner.
        """
        if self.existing_user and self.data.get('confirm_use_existing', '') == 'on':
            # Do not create new Contact
            try:
                # Link Contact to new Partner
                contact = self.existing_user.partner_contact
                contact.partners.add(self.partner)
                # TODO: Send mail to contact informing him/her about the new Partner
            except Contact.DoesNotExist:
                # Not yet a 'Contact-User'
                contact = super().save(commit=False)
                contact.title = self.existing_user.contributor.title
                contact.user = self.existing_user
                contact.save()
                contact.partners.add(self.partner)
                # TODO: Send mail to contact informing him/her about the new Partner
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
            title=self.cleaned_data['title'],
            kind=self.cleaned_data['kind']
        )
        contact.generate_key()
        contact.save()
        contact.partners.add(self.partner)
        # TODO: Send mail to contact to let him/her activate account
        return contact


class ContactFormset(forms.BaseModelFormSet):
    """
    Use custom formset to make sure the delete action will not delete an entire Contact
    if the Contact still has relations with other Partners.
    """
    def __init__(self, *args, **kwargs):
        """
        Partner is a required argument to tell the formset which Partner the Contact
        is being edited for in the current form.
        """
        self.partner = kwargs.pop('partner')
        super().__init__(*args, **kwargs)

    def delete_existing(self, obj, commit=True):
        '''Deletes an existing model instance.'''
        if commit:
            obj.delete_or_remove_partner(self.partner)


class PromoteToPartnerForm(forms.ModelForm):
    address = forms.CharField(widget=forms.Textarea(), required=False)
    acronym = forms.CharField()

    class Meta:
        model = ProspectivePartner
        fields = (
            'kind',
            'institution_name',
            'country',
        )

    def promote_to_partner(self):
        # Create new instances
        institution = Institution(
            kind=self.cleaned_data['kind'],
            name=self.cleaned_data['institution_name'],
            acronym=self.cleaned_data['acronym'],
            address=self.cleaned_data['address'],
            country=self.cleaned_data['country']
        )
        institution.save()
        partner = Partner(
            institution=institution,
            main_contact=None
        )
        partner.save()

        # Close Prospect
        self.instance.status = PROSPECTIVE_PARTNER_PROCESSED
        self.instance.save()
        return (partner, institution,)


class PromoteToContactForm(forms.ModelForm):
    """
    This form is used to create a new `partners.Contact`
    """
    contact_types = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                              choices=CONTACT_TYPES, required=False)

    class Meta:
        model = ProspectiveContact
        fields = (
            'title',
            'first_name',
            'last_name',
            'email',
        )

    def clean_email(self):
        """
        Check if email address is already used.
        """
        email = self.cleaned_data['email']
        if User.objects.filter(Q(email=email) | Q(username=email)).exists():
            self.add_error('email', 'This emailadres has already been used.')
        return email

    def promote_contact(self, partner):
        """
        Promote ProspectiveContact's to Contact's related to a certain Partner.
        The status update after promotion is handled outside this method, in the Partner model.
        """
        # How to handle empty instances?

        if self.errors:
            return forms.ValidationError  # Is this a valid exception?

        # Create a new User and Contact linked to the partner given
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
            title=self.cleaned_data['title'],
            kind=self.cleaned_data['contact_types']
        )
        contact.save()
        contact.partners.add(partner)
        return contact


class PromoteToContactFormset(forms.BaseModelFormSet):
    """
    This is a formset to process multiple `PromoteToContactForm`s at the same time
    designed for the 'promote prospect to partner' action.
    """
    def clean(self):
        """
        Check if all CONTACT_TYPES are assigned to at least one contact.
        """
        contact_type_keys = list(dict(CONTACT_TYPES).keys())
        for form in self.forms:
            try:
                contact_types = form.cleaned_data['contact_types']
            except KeyError:
                # Form invalid for `contact_types`
                continue

            for _type in contact_types:
                try:
                    contact_type_keys.remove(_type)
                except ValueError:
                    # Type-key already removed
                    continue
            if not contact_type_keys:
                break
        if contact_type_keys:
            # Add error to all forms if not all CONTACT_TYPES are assigned
            for form in self.forms:
                form.add_error('contact_types', ("Not all contact types have been"
                                                 " divided over the contacts yet."))

    def save(self, *args, **kwargs):
        raise DeprecationWarning(("This formset is not meant to used with the default"
                                  " `save` method. User the `promote_contacts` instead."))

    def promote_contacts(self, partner):
        """
        Promote ProspectiveContact's to Contact's related to a certain Partner.
        """
        contacts = []
        for form in self.forms:
            contacts.append(form.promote_contact(partner))
        partner.main_contact = contacts[0]
        partner.save()
        return contacts


class ProspectivePartnerForm(forms.ModelForm):
    """
    This form is used to internally add a ProspectivePartner.
    If an external agent requests membership of the SPB,
    the MembershipQueryForm below is used instead.
    """
    class Meta:
        model = ProspectivePartner
        fields = ('kind', 'institution_name', 'country')


class ProspectiveContactForm(forms.ModelForm):
    class Meta:
        model = ProspectiveContact
        fields = '__all__'
        widgets = {'prospartner': forms.HiddenInput()}


class EmailProspectivePartnerContactForm(forms.Form):
    email_subject = forms.CharField(widget=forms.Textarea(),
                                    initial='SciPost Supporting Partners Board')
    message = forms.CharField(widget=forms.Textarea(), required=False)
    include_SPB_summary = forms.BooleanField(
        required=False, initial=False,
        label='include SPB summary with message')

    def __init__(self, *args, **kwargs):
        super(EmailProspectivePartnerContactForm, self).__init__(*args, **kwargs)
        self.fields['email_subject'].widget.attrs.update(
            {'rows': 1})
        self.fields['message'].widget.attrs.update(
            {'placeholder': 'Write your message in this box (optional).'})


class ProspectivePartnerEventForm(forms.ModelForm):
    class Meta:
        model = ProspectivePartnerEvent
        fields = ('event', 'comments')
        widgets = {
            'comments': forms.Textarea(attrs={'cols': 16, 'rows': 3}),
        }


class MembershipQueryForm(forms.Form):
    """
    This form is to be used by an agent of the prospective Partner,
    in order to request more information about potentially joining the SPB.
    """
    title = forms.ChoiceField(choices=TITLE_CHOICES, label='* Your title')
    first_name = forms.CharField(label='* Your first name', max_length=100)
    last_name = forms.CharField(label='* Your last name', max_length=100)
    email = forms.EmailField(label='* Your email address')
    role = forms.CharField(label='* Your role in your organization')
    partner_kind = forms.ChoiceField(choices=PARTNER_KINDS, label='* Partner kind')
    institution_name = forms.CharField(label='* Name of your institution')
    country = LazyTypedChoiceField(
        choices=countries, label='* Country', initial='NL',
        widget=CountrySelectWidget(layout=(
            '{widget}<img class="country-select-flag" id="{flag_id}"'
            ' style="margin: 6px 4px 0" src="{country.flag}">')))
    captcha = ReCaptchaField(attrs={'theme': 'clean'}, label='*Please verify to continue:')
