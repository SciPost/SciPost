__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import PetitionSignatory

from scipost.models import Contributor


class SignPetitionForm(forms.ModelForm):

    class Meta:
        model = PetitionSignatory
        fields = ['title', 'first_name', 'last_name',
                  'email', 'country_of_employment', 'affiliation']

    def __init__(self, *args, **kwargs):
        self.petition = kwargs.pop('petition', False)
        self.current_user = kwargs.pop('current_user', False)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        petition = self.petition
        if not petition:
            return email

        if self.instance.id:
            return email

        if self.current_user.is_authenticated:
            if self.current_user.email != email:
                self.add_error('email', 'This email address is not associated to your account')
        else:
            if Contributor.objects.filter(user__email=email).exists():
                self.add_error('email', ('This email address is associated to a Contributor; please '
                                         'login to sign the petition'))
        if PetitionSignatory.objects.filter(petition=petition, email=email).exists():
            self.add_error('email', ('This email address is already associated to a '
                                     'signature for this petition'))

        return email
