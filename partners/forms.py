from django import forms
from django.contrib.auth.models import User
from django.db.models import Q

from captcha.fields import ReCaptchaField
from django_countries import countries
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import LazyTypedChoiceField

from .constants import PARTNER_KINDS, PROSPECTIVE_PARTNER_PROCESSED, CONTACT_TYPES
from .models import Partner, ProspectivePartner, ProspectiveContact, ProspectivePartnerEvent,\
                    Institution, Contact

from scipost.models import TITLE_CHOICES


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
            username=self.cleaned_data['email']
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
