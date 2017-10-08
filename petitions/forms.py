from django import forms

from captcha.fields import ReCaptchaField

from .models import PetitionSignatory


class SignPetitionForm(forms.ModelForm):
    captcha = ReCaptchaField(attrs={'theme': 'clean'}, label='*Please verify to continue:')

    class Meta:
        model = PetitionSignatory
        fields = ['title', 'first_name', 'last_name',
                  'email', 'country_of_employment', 'affiliation']
