__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import Profile, ProfileEmail


class ProfileForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = ['title', 'first_name', 'last_name',
                  'discipline', 'expertises', 'orcid_id', 'webpage',
                  'accepts_SciPost_emails', 'accepts_refereeing_requests']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].initial = self.instance.email

    def clean_email(self):
        """Check that the email isn't yet associated to an existing Profile."""
        cleaned_email = self.cleaned_data['email']
        if ProfileEmail.objects.filter(email=cleaned_email).exclude(profile__id=self.instance.id).exists():
            raise forms.ValidationError('A Profile with this email already exists.')
        return cleaned_email

    def save(self):
        profile = super().save()
        profile.emails.update(primary=False)
        email, __ = ProfileEmail.objects.get_or_create(
            profile=profile, email=self.cleaned_data['email'])
        profile.emails.filter(id=email.id).update(primary=True, still_valid=True)
        return profile


class ProfileEmailForm(forms.ModelForm):

    class Meta:
        model = ProfileEmail
        fields = ['email', 'still_valid']

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        """Check if profile/email combination exists."""
        email = self.cleaned_data['email']
        if self.profile.emails.filter(email=email).exists():
            self.add_error('email', 'This profile/email pair is already defined.')
        return email

    def save(self):
        """Save to a profile."""
        self.instance.profile = self.profile
        return super().save()
