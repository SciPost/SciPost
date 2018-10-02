__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import Profile, AlternativeEmail


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['title', 'first_name', 'last_name', 'email',
                  'discipline', 'expertises', 'orcid_id', 'webpage',
                  'accepts_SciPost_emails', 'accepts_refereeing_requests']

    def clean_email(self):
        """
        Check that the email isn't yet associated to an existing Profile
        (via either the email field or the m2m-related alternativeemails).
        """
        cleaned_email = self.cleaned_data['email']
        if Profile.objects.filter(email=cleaned_email).exists():
            raise forms.ValidationError(
                'A Profile with this email (as primary email) already exists.')
        elif AlternativeEmail.objects.filter(email=cleaned_email).exists():
            raise forms.ValidationError(
                'A Profile with this email (as alternative email) already exists.')
        return cleaned_email


class AlternativeEmailForm(forms.ModelForm):

    class Meta:
        model = AlternativeEmail
        fields = ['email', 'still_valid']


class SearchTextForm(forms.Form):
    text = forms.CharField(label='')
