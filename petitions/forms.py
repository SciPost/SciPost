from django import forms

from captcha.fields import ReCaptchaField

from .models import PetitionSignatory

from scipost.models import Contributor


class SignPetitionForm(forms.ModelForm):
    captcha = ReCaptchaField(attrs={'theme': 'clean'}, label='*Please verify to continue:')

    class Meta:
        model = PetitionSignatory
        fields = ['petition', 'title', 'first_name', 'last_name',
                  'email', 'country_of_employment', 'affiliation']
        widgets = {'petition': forms.HiddenInput()}


    def clean_email(self):
        email = self.cleaned_data['email']
        petition = self.cleaned_data['petition']
        if self.instance.id:
            return email

        if Contributor.objects.filter(user__email=email).exists():
            self.add_error('email', ('This email address is associated to a Contributor; please '
                                     'login to sign the petition'))
        elif PetitionSignatory.objects.filter(petition=petition, email=email).exists():
            self.add_error('email', ('This email address is already associated to a '
                                     'signature for this petition'))
