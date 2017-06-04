from django import forms

from captcha.fields import ReCaptchaField
from django_countries import countries
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import LazyTypedChoiceField

from .constants import PARTNER_KINDS
from .models import Partner, ProspectivePartner, ProspectiveContact, \
    ProspectivePartnerEvent, MembershipAgreement

from scipost.models import TITLE_CHOICES


class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(PartnerForm, self).__init__(*args, **kwargs)
        self.fields['institution_address'].widget = forms.Textarea({'rows': 8, })


class ProspectivePartnerForm(forms.ModelForm):
    """
    This form is used to internally add a ProspectivePartner.
    If an external agent requests membership of the SPB,
    the MembershipQueryForm below is used instead.
    """
    class Meta:
        model = ProspectivePartner
        exclude = ['date_received', 'date_processed']
        widgets = {'status': forms.HiddenInput()}


class ProspectiveContactForm(forms.ModelForm):
    class Meta:
        model = ProspectiveContact
        fields = '__all__'
        widgets = {'prospartner': forms.HiddenInput()}


class ProspectivePartnerEventForm(forms.ModelForm):
    class Meta:
        model = ProspectivePartnerEvent
        exclude = ['prospartner', 'noted_on', 'noted_by']
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
