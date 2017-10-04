from django import forms

from .models import PetitionSignatory


class SignPetitionForm(forms.ModelForm):
    class Meta:
        model = PetitionSignatory
        fields = ['title', 'first_name', 'last_name',
                  'email', 'country_of_employment', 'affiliation']
