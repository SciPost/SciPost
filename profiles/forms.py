__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.shortcuts import get_object_or_404

from .models import Profile, ProfileEmail

from scipost.models import Contributor
from invitations.models import RegistrationInvitation
from journals.models import UnregisteredAuthor
from submissions.models import RefereeInvitation


class ProfileForm(forms.ModelForm):
    email = forms.EmailField()
    # If the Profile is created from an existing object (so we can update the object):
    instance_from_type = forms.CharField(max_length=32, required=False)
    instance_pk = forms.IntegerField(required=False)

    class Meta:
        model = Profile
        fields = ['title', 'first_name', 'last_name',
                  'discipline', 'expertises', 'orcid_id', 'webpage',
                  'accepts_SciPost_emails', 'accepts_refereeing_requests',
                  'instance_from_type', 'instance_pk']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].initial = self.instance.email
        self.fields['instance_from_type'].widget = forms.HiddenInput()
        self.fields['instance_pk'].widget = forms.HiddenInput()

    def clean_email(self):
        """Check that the email isn't yet associated to an existing Profile."""
        cleaned_email = self.cleaned_data['email']
        if ProfileEmail.objects.filter(email=cleaned_email).exclude(profile__id=self.instance.id).exists():
            raise forms.ValidationError('A Profile with this email already exists.')
        return cleaned_email

    def clean_instance_from_type(self):
        """
        Check that only recognized types are used.
        """
        cleaned_instance_from_type = self.cleaned_data['instance_from_type']
        if cleaned_instance_from_type not in ['', 'contributor', 'unregistered_author',
                                              'refereeinvitation', 'registrationinvitation']:
            raise forms.ValidationError('The from_type hidden field is inconsistent.')
        return cleaned_instance_from_type

    def save(self):
        profile = super().save()
        profile.emails.update(primary=False)
        email, __ = ProfileEmail.objects.get_or_create(
            profile=profile, email=self.cleaned_data['email'])
        profile.emails.filter(id=email.id).update(primary=True, still_valid=True)
        instance_pk = self.cleaned_data['instance_pk']
        if instance_pk:
            print('%s, %s' % (instance_pk, self.cleaned_data['instance_from_type']))
            if self.cleaned_data['instance_from_type'] == 'contributor':
                contributor = get_object_or_404(Contributor, pk=instance_pk)
                contributor.profile = profile
                contributor.save()
            elif self.cleaned_data['instance_from_type'] == 'unregistered_author':
                unreg_auth = get_object_or_404(UnregisteredAuthor, pk=instance_pk)
                unreg_auth.profile = profile
                unreg_auth.save()
            elif self.cleaned_data['instance_from_type'] == 'refereeinvitation':
                ref_inv = get_object_or_404(RefereeInvitation, pk=instance_pk)
                ref_inv.profile = profile
                ref_inv.save()
            elif self.cleaned_data['instance_from_type'] == 'registrationinvitation':
                reg_inv = get_object_or_404(RegistrationInvitation, pk=instance_pk)
                reg_inv.profile = profile
                reg_inv.save()
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
