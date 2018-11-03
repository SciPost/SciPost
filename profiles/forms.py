__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.core.exceptions import ObjectDoesNotExist
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
        if cleaned_instance_from_type not in ['', 'contributor', 'unregisteredauthor',
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
            if self.cleaned_data['instance_from_type'] == 'contributor':
                contributor = get_object_or_404(Contributor, pk=instance_pk)
                contributor.profile = profile
                contributor.save()
            elif self.cleaned_data['instance_from_type'] == 'unregisteredauthor':
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


class ProfileMergeForm(forms.Form):
    to_merge = forms.IntegerField()
    to_merge_into = forms.IntegerField()

    def save(self):
        """
        Perform the actual merge: save all data from to-be-deleted profile
        into the one to be kept.
        """
        profile_to_merge = get_object_or_404(Profile, pk=self.cleaned_data['to_merge'])
        profile_to_merge_into = get_object_or_404(Profile, pk=self.cleaned_data['to_merge_into'])
        # Model fields:
        if profile_to_merge.expertises:
            for expertise in profile_to_merge.expertises:
                if expertise not in profile_to_merge_into.expertises:
                    profile_to_merge_into.expertises.append(expertise)
        if profile_to_merge.orcid_id and (profile_to_merge_into.orcid_id is None):
            profile_to_merge_into.orcid_id = profile_to_merge.orcid_id
        if profile_to_merge.webpage and (profile_to_merge_into.webpage is None):
            profile_to_merge_into.webpage = profile_to_merge.webpage
        for topic in profile_to_merge.topics.all():
            profile_to_merge_into.topics.add(topic)
        # Related objects:
        for profileemail in profile_to_merge.emails.all():
            if profileemail.email not in profile_to_merge_into.emails.all():
                print('Adding email %s' % profileemail.email)
                profileemail.primary = False
                profileemail.profile = profile_to_merge_into
                profileemail.save()
        try:
            contrib_into = profile_to_merge_into.contributor
        except ObjectDoesNotExist:
            try:
                contrib = profile_to_merge.contributor
                contrib.profile = profile_to_merge_into
                contrib.save()
            except ObjectDoesNotExist:
                pass
        try:
            unreg_auth = profile_to_merge.unregisteredauthor
            try:
                profile_to_merge_into.unregisteredauthor.merge(unreg_auth.id)
            except ObjectDoesNotExist:
                pass
        except ObjectDoesNotExist:
            pass
        for refinv in profile_to_merge.refereeinvitation_set.all():
            refinv.profile = profile_to_merge_into
            refinv.save()
        for reginv in profile_to_merge.registrationinvitation_set.all():
            reginv.profile = profile_to_merge_into
            reginv.save()
        # Delete the deprecated object:
        profile_to_merge.delete()


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
