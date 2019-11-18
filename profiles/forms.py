__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from ajax_select.fields import AutoCompleteSelectField
from dal import autocomplete

from common.forms import ModelChoiceFieldwithid
from invitations.models import RegistrationInvitation
from organizations.models import Organization
from scipost.models import Contributor
from submissions.models import RefereeInvitation

from .models import Profile, ProfileEmail, Affiliation


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False)
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
        if cleaned_email and ProfileEmail.objects.filter(
                email=cleaned_email).exclude(profile__id=self.instance.id).exists():
            raise forms.ValidationError('A Profile with this email already exists.')
        return cleaned_email

    def clean_instance_from_type(self):
        """
        Check that only recognized types are used.
        """
        cleaned_instance_from_type = self.cleaned_data['instance_from_type']
        if cleaned_instance_from_type not in ['', 'contributor',
                                              'refereeinvitation', 'registrationinvitation']:
            raise forms.ValidationError('The from_type hidden field is inconsistent.')
        return cleaned_instance_from_type

    def save(self):
        profile = super().save()
        if self.cleaned_data['email']:
            profile.emails.update(primary=False)
            email, __ = ProfileEmail.objects.get_or_create(
                profile=profile, email=self.cleaned_data['email'])
            profile.emails.filter(id=email.id).update(primary=True, still_valid=True)
        instance_pk = self.cleaned_data['instance_pk']
        if instance_pk:
            if self.cleaned_data['instance_from_type'] == 'contributor':
                Contributor.objects.filter(pk=instance_pk).update(profile=profile)
            elif self.cleaned_data['instance_from_type'] == 'refereeinvitation':
                RefereeInvitation.objects.filter(pk=instance_pk).update(profile=profile)
            elif self.cleaned_data['instance_from_type'] == 'registrationinvitation':
                RegistrationInvitation.objects.filter(pk=instance_pk).update(profile=profile)
        return profile


class SimpleProfileForm(ProfileForm):
    """
    Simple version of ProfileForm, displaying only required fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expertises'].widget = forms.HiddenInput()
        self.fields['orcid_id'].widget = forms.HiddenInput()
        self.fields['webpage'].widget = forms.HiddenInput()
        self.fields['accepts_SciPost_emails'].widget = forms.HiddenInput()
        self.fields['accepts_refereeing_requests'].widget = forms.HiddenInput()


class ProfileMergeForm(forms.Form):
    to_merge = ModelChoiceFieldwithid(queryset=Profile.objects.all(), empty_label=None)
    to_merge_into = ModelChoiceFieldwithid(queryset=Profile.objects.all(), empty_label=None)

    def clean(self):
        """
        To merge Profiles, they must be distinct, and it must not be the
        case that they both are associated to a Contributor instance
        (which would mean two Contributor objects for the same person).
        """
        data = super().clean()
        if self.cleaned_data['to_merge'] == self.cleaned_data['to_merge_into']:
            self.add_error(None, 'A Profile cannot be merged into itself.')
        if self.cleaned_data['to_merge'].has_active_contributor and \
           self.cleaned_data['to_merge_into'].has_active_contributor:
            self.add_error(None, 'Each of these two Profiles has an active Contributor. '
                           'Merge the Contributors first.\n'
                           'If these are distinct people or if two separate '
                           'accounts are needed, a ProfileNonDuplicate instance should be created; '
                           'contact techsupport.')
        return data

    def save(self):
        """
        Perform the actual merge: save all data from to-be-deleted profile
        into the one to be kept.
        """
        profile = self.cleaned_data['to_merge_into']
        profile_old = self.cleaned_data['to_merge']

        # Merge information from old to new Profile.
        profile.expertises = list(
            set(profile_old.expertises or []) | set(profile.expertises or []))
        if profile.orcid_id is None:
            profile.orcid_id = profile_old.orcid_id
        if profile.webpage is None:
            profile.webpage = profile_old.webpage
        if profile_old.has_active_contributor and not profile.has_active_contributor:
            profile.contributor = profile_old.contributor
        profile.save()  # Save all the field updates.

        profile.topics.add(*profile_old.topics.all())

        # Merge email
        profile_old.emails.exclude(
            email__in=profile.emails.values_list('email', flat=True)).update(
            primary=False, profile=profile)

        # Move all affiliations to the "new" profile
        profile_old.affiliations.all().update(profile=profile)

        # Move all PublicationAuthorsTable instances to the "new" profile
        profile_old.publicationauthorstable_set.all().update(profile=profile)

        # Move all invitations to the "new" profile
        profile_old.refereeinvitation_set.all().update(profile=profile)
        profile_old.registrationinvitation_set.all().update(profile=profile)

        # Move all PotentialFellowships to the "new" profile
        profile_old.potentialfellowship_set.all().update(profile=profile)

        profile_old.delete()
        return Profile.objects.get(id=profile.id)  # Retrieve again because of all the db updates.


class ProfileEmailForm(forms.ModelForm):

    class Meta:
        model = ProfileEmail
        fields = ['email', 'still_valid', 'primary']

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


class ProfileSelectForm(forms.Form):
    profile = AutoCompleteSelectField(
        'profile_lookup',
        help_text=('Start typing, and select from the popup.'),
        show_help_text=False)


class AffiliationForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='/organizations/organization-autocomplete',
            attrs={'data-html': True}
        )
    )

    class Meta:
        model = Affiliation
        fields = ['profile', 'organization', 'category',
                  'description', 'date_from', 'date_until']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile'].widget = forms.HiddenInput()
