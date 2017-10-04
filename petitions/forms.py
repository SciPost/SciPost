from django import forms

from .models import PetitionSignatory


class SignPetitionForm(forms.ModelForm):
    class Meta:
        model = PetitionSignatory
        fields = ['title', 'first_name', 'last_name',
                  'email', 'country_of_employment', 'affiliation']


    # title = forms.ChoiceField(choices=TITLE_CHOICES, label='* Title')
    # first_name = forms.CharField(label='* First name', max_length=100)
    # last_name = forms.CharField(label='* Last name', max_length=100)
    # email = forms.EmailField(label='* Email address')
    # country_of_employment = LazyTypedChoiceField(
    #     choices=countries, label='* Country of employment', initial='NL',
    #     widget=CountrySelectWidget(layout=(
    #         '{widget}<img class="country-select-flag" id="{flag_id}"'
    #         ' style="margin: 6px 4px 0" src="{country.flag}">')))
    # affiliation = forms.CharField(label='* Affiliation', max_length=300)
    # verification_key = forms.CharField(max_length=40, widget=forms.HiddenInput(), required=False)
    # captcha = ReCaptchaField(attrs={'theme': 'clean'}, label='*Please verify to continue:')
