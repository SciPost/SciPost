__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from ajax_select.fields import AutoCompleteSelectField

from captcha.fields import ReCaptchaField
from django_countries import countries
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import LazyTypedChoiceField

from .constants import PARTNER_KINDS, PROSPECTIVE_PARTNER_PROCESSED, CONTACT_TYPES,\
                       PARTNER_STATUS_UPDATE, REQUEST_PROCESSED, REQUEST_DECLINED, CONTACT_GENERAL
from .models import Partner, ProspectivePartner, ProspectiveContact, ProspectivePartnerEvent,\
                    Contact, PartnerEvent, MembershipAgreement, ContactRequest,\
                    PartnersAttachment
from .utils import PartnerUtils

from scipost.models import TITLE_CHOICES


class MembershipAgreementForm(forms.ModelForm):
    class Meta:
        model = MembershipAgreement
        fields = (
            'partner',
            'status',
            'date_requested',
            'start_date',
            'end_date',
            'duration',
            'offered_yearly_contribution'
        )
        widgets = {
            'start_date': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            'end_date': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            'date_requested': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        }

    def save(self, current_user, commit=True):
        agreement = super().save(commit=False)
        if commit:
            if agreement.partner and not self.instance.id:
                # Create PartnerEvent if Agreement is new
                event = PartnerEvent(
                    partner=agreement.partner,
                    event=PARTNER_STATUS_UPDATE,
                    comments='Membership Agreement added with start date %s' % agreement.start_date,
                    noted_by=current_user
                )
                event.save()
            # Save agreement afterwards to be able to detect edit/add difference
            agreement.save()
        return agreement


class ActivationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = []

    description = forms.CharField(max_length=256, label="Title", required=False,
                                  widget=forms.TextInput(attrs={
                                    'placeholder': 'E.g.: Legal Agent at Stanford University'}))
    kind = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, label="Contact type",
                                     choices=CONTACT_TYPES)
    password_new = forms.CharField(label='* Password', widget=forms.PasswordInput())
    password_verif = forms.CharField(label='* Verify password', widget=forms.PasswordInput(),
                                     help_text='Your password must contain at least 8 characters')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['kind'].initial = self.instance.partner_contact.kind
        except Contact.DoesNotExist:
            pass

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

    @transaction.atomic
    def activate_user(self):
        if self.errors:
            return forms.ValidationError

        # Activate account
        self.instance.is_active = True
        self.instance.set_password(self.cleaned_data['password_new'])
        self.instance.save()

        # Set fields for Contact
        self.instance.partner_contact.description = self.cleaned_data['description']
        self.instance.partner_contact.kind = self.cleaned_data['kind']
        self.instance.partner_contact.save()

        # Add permission groups to user
        group = Group.objects.get(name='Partners Accounts')
        self.instance.groups.add(group)
        return self.instance


class PartnerEventForm(forms.ModelForm):
    class Meta:
        model = PartnerEvent
        fields = (
            'event',
            'comments',
        )


class PartnerForm(forms.ModelForm):
    organization = AutoCompleteSelectField('organization_lookup')

    class Meta:
        model = Partner
        fields = (
            'organization',
            'status',
            'main_contact'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['main_contact'].queryset = self.instance.contact_set.all()


class RequestContactForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = (
            'email',
            'title',
            'first_name',
            'last_name',
            'kind',
        )


class ProcessRequestContactForm(RequestContactForm):
    decision = forms.ChoiceField(choices=((None, 'No decision'), ('accept', 'Accept'), ('decline', 'Decline')),
                                 widget=forms.RadioSelect, label='Accept or Decline')

    class Meta:
        model = ContactRequest
        fields = RequestContactForm.Meta.fields + ('partner',)

    def process_request(self, current_user):
        if self.cleaned_data['decision'] == 'accept':
            self.instance.status = REQUEST_PROCESSED
            self.instance.save()
            contactForm = NewContactForm({
                'title': self.cleaned_data['title'],
                'email': self.cleaned_data['email'],
                'first_name': self.cleaned_data['first_name'],
                'last_name': self.cleaned_data['last_name'],
                'kind': self.cleaned_data['kind'],
            }, partner=self.cleaned_data['partner'])
            contactForm.is_valid()
            contactForm.save(current_user=current_user)
        elif self.cleaned_data['decision'] == 'decline':
            self.instance.status = REQUEST_DECLINED
            self.instance.save()


class RequestContactFormSet(forms.BaseModelFormSet):
    def process_requests(self, current_user):
        """
        Process all requests if status is eithter accept or decline.
        """
        for form in self.forms:
            form.process_request(current_user=current_user)


class ContactForm(forms.ModelForm):
    """
    This Contact form is mainly used for editing Contact instances.
    """
    class Meta:
        model = Contact
        fields = (
            'kind',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['kind'].required = False


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

    @transaction.atomic
    def save(self, current_user, commit=True):
        """
        If existing user is found, add it to the Partner.
        """
        if self.existing_user and self.data.get('confirm_use_existing', '') == 'on':
            # Do not create new Contact
            try:
                # Link Contact to new Partner
                contact = self.existing_user.partner_contact
                contact.partners.add(self.partner)
            except Contact.DoesNotExist:
                # Not yet a 'Contact-User'
                contact = super().save(commit=False)
                contact.title = self.existing_user.contributor.title
                contact.user = self.existing_user
                contact.save()
                contact.partners.add(self.partner)
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

        # Send email for activation
        PartnerUtils.load({'contact': contact})
        PartnerUtils.email_contact_new_for_activation(current_user=current_user)
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
    organization = AutoCompleteSelectField('organization_lookup')

    class Meta:
        model = ProspectivePartner
        fields = (
            'kind',
            'institution_name',
            'country',
        )

    def promote_to_partner(self, current_user):
        partner = Partner(
            organization=self.cleaned_data['organization'],
            main_contact=None
        )
        partner.save()
        event = PartnerEvent(
            partner=partner,
            event=PARTNER_STATUS_UPDATE,
            comments='ProspectivePartner has been upgraded to Partner by %s %s'
                     % (current_user.first_name, current_user.last_name),
            noted_by=current_user
        )
        event.save()

        # Close Prospect
        self.instance.status = PROSPECTIVE_PARTNER_PROCESSED
        self.instance.save()
        return partner


class PromoteToContactForm(forms.ModelForm):
    """
    This form is used to create a new `partners.Contact`
    """
    promote = forms.BooleanField(label='Activate/Promote this contact', initial=True,
                                 required=False)
    kind = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, initial=[CONTACT_GENERAL],
                                     label='Contact types', choices=CONTACT_TYPES, required=False)

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
        if not self.cleaned_data.get('promote', False):
            # Don't promote the Contact
            return email
        if User.objects.filter(Q(email=email) | Q(username=email)).exists():
            self.add_error('email', 'This emailadres has already been used.')
        return email

    @transaction.atomic
    def promote_contact(self, partner, current_user):
        """
        Promote ProspectiveContact's to Contact's related to a certain Partner.
        The status update after promotion is handled outside this method, in the Partner model.
        """
        if not self.cleaned_data.get('promote', False):
            # Don't promote the Contact
            return

        # How to handle empty instances?
        if self.errors:
            return forms.ValidationError  # Is this a valid exception?

        # Create a new User and Contact linked to the partner given
        contact_form = NewContactForm(self.cleaned_data, partner=partner)
        if contact_form.is_valid():
            return contact_form.save(current_user=current_user)
        raise forms.ValidationError('NewContactForm invalid. Please contact Admin.')


class PromoteToContactFormset(forms.BaseModelFormSet):
    """
    This is a formset to process multiple `PromoteToContactForm`s at the same time
    designed for the 'promote prospect to partner' action.
    """
    def save(self, *args, **kwargs):
        raise DeprecationWarning(("This formset is not meant to used with the default"
                                  " `save` method. User the `promote_contacts` instead."))

    @transaction.atomic
    def promote_contacts(self, partner, current_user):
        """
        Promote ProspectiveContact's to Contact's related to a certain Partner.
        """
        contacts = []
        for form in self.forms:
            new_contact = form.promote_contact(partner, current_user)
            if new_contact:
                contacts.append(new_contact)
        try:
            partner.main_contact = contacts[0]
        except IndexError:
            # No contacts at all means no main-contact as well...
            pass
        partner.save()
        return contacts


ContactModelFormset = forms.modelformset_factory(ProspectiveContact, PromoteToContactForm,
                                                 formset=PromoteToContactFormset, extra=0)


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


class PartnersAttachmentForm(forms.ModelForm):
    class Meta:
        model = PartnersAttachment
        fields = (
            'name',
            'attachment',
        )

    def save(self, to_object, commit=True):
        """
        This custom save method will automatically assign the file to the object
        given when its a valid instance type.
        """
        attachment = super().save(commit=False)

        # Formset's might save an empty Instance
        if not attachment.name or not attachment.attachment:
            return None

        if isinstance(to_object, MembershipAgreement):
            attachment.agreement = to_object
        else:
            raise forms.ValidationError('You cannot save Attachment to this type of object.')
        if commit:
            attachment.save()
        return attachment


class PartnersAttachmentFormSet(forms.BaseModelFormSet):
    def save(self, to_object, commit=True):
        """
        This custom save method will automatically assign the file to the object
        given when its a valid instance type.
        """
        returns = []
        for form in self.forms:
            returns.append(form.save(to_object))
        return returns
