__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.contrib import messages
from django.db.models import Q

from journals.models import Publication
from scipost.models import Contributor
from submissions.models import Submission

from . import constants
from .models import RegistrationInvitation, CitationNotification

from profiles.models import Profile
from submissions.models import Submission

from dal import autocomplete


class AcceptRequestMixin:
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)


class RegistrationInvitationFilterForm(forms.Form):
    term = forms.CharField(help_text="You may search on arXiv identifier, DOI or last name.")

    def search(self, qs):
        term = self.cleaned_data.get('term')
        return qs.filter(
            Q(last_name__icontains=term) |
            Q(citation_notifications__submission__preprint__identifier_w_vn_nr__icontains=term) |
            Q(citation_notifications__publication__doi_label__icontains=term))


class SuggestionSearchForm(forms.Form):
    last_name = forms.CharField()

    def search(self):
        last_name = self.cleaned_data.get('last_name')

        if last_name:
            contributors = Contributor.objects.filter(user__last_name__icontains=last_name)
            invitations = RegistrationInvitation.objects.filter(last_name__icontains=last_name)
            declines = RegistrationInvitation.objects.declined().filter(
                last_name__icontains=last_name)
            return contributors, invitations, declines
        return Contributor.objects.none(), RegistrationInvitation.objects.none()


class CitationNotificationForm(AcceptRequestMixin, forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=Submission.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='/submissions/submission-autocomplete',
            attrs={'data-html': True}
        ),
        required=False
    )
    publication = forms.ModelChoiceField(
        queryset=Publication.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='/journals/publication-autocomplete',
            attrs={'data-html': True}
        ),
        required=False
    )

    class Meta:
        model = CitationNotification
        fields = (
            'contributor',
            'submission',
            'publication')

    def __init__(self, *args, **kwargs):
        contributors = kwargs.pop('contributors')
        super().__init__(*args, **kwargs)
        if contributors:
            self.fields['contributor'].queryset = contributors
            self.fields['contributor'].empty_label = None
        else:
            self.fields['contributor'].queryset = Contributor.objects.none()

    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        if not data.get('submission') and not data.get('publication'):
            self.add_error('submission', 'Either a Submission or Publication has to be filled out')
            self.add_error('publication', 'Either a Submission or Publication has to be filled out')

    def save(self, *args, **kwargs):
        if not hasattr(self.instance, 'created_by'):
            self.instance.created_by = self.request.user
        return super().save(*args, **kwargs)


class CitationNotificationProcessForm(AcceptRequestMixin, forms.ModelForm):
    class Meta:
        model = CitationNotification
        fields = ()

    def get_all_notifications(self):
        return self.instance.related_notifications().unprocessed()


class RegistrationInvitationAddCitationForm(AcceptRequestMixin, forms.ModelForm):
    cited_in_submissions = forms.ModelMultipleChoiceField(
        queryset=Submission.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='/submissions/submission-autocomplete',
            attrs={'data-html': True}
        ),
        required=False
    )
    cited_in_publications = forms.ModelMultipleChoiceField(
        queryset=Publication.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='/journals/publication-autocomplete',
            attrs={'data-html': True}
        ),
        required=False
    )

    class Meta:
        model = RegistrationInvitation
        fields = ()

    def save(self, *args, **kwargs):
        if kwargs.get('commit', True):
            updated = 0
            # Save the Submission notifications
            submissions = Submission.objects.filter(
                id__in=self.cleaned_data['cited_in_submissions'])
            for submission in submissions:
                __, _updated = CitationNotification.objects.get_or_create(
                    invitation=self.instance,
                    submission=submission,
                    defaults={'created_by': self.request.user})
                updated += 1 if _updated else 0

            # Save the Publication notifications
            publications = Publication.objects.filter(
                id__in=self.cleaned_data['cited_in_publications'])
            for publication in publications:
                __, _updated = CitationNotification.objects.get_or_create(
                    invitation=self.instance,
                    publication=publication,
                    defaults={'created_by': self.request.user})
                updated += 1 if _updated else 0
            if updated > 0:
                self.instance.status = constants.STATUS_SENT_AND_EDITED
                self.instance.save()
            messages.success(self.request, '{} Citation Notification(s) added.'.format(updated))
        return self.instance


class RegistrationInvitationMergeForm(AcceptRequestMixin, forms.ModelForm):
    """Merge RegistrationInvitations.

    This form will merge the instance with any other RegistrationInvitation selected
    into a single RegistrationInvitation.
    """

    invitation = forms.ModelChoiceField(queryset=RegistrationInvitation.objects.none(),
                                        label="Invitation to merge with")

    class Meta:
        model = RegistrationInvitation
        fields = ()

    def __init__(self, *args, **kwargs):
        """Update queryset according to the passed instance."""
        super().__init__(*args, **kwargs)
        self.fields['invitation'].queryset = RegistrationInvitation.objects.no_response().filter(
            last_name__icontains=self.instance.last_name).exclude(id=self.instance.id)

    def save(self, *args, **kwargs):
        """Merge the two RegistationInvitations into one."""
        if kwargs.get('commit', True):
            # Pick the right Invitation, with the most up-to-date invitation_key
            selected_invitation = self.cleaned_data['invitation']
            if not selected_invitation.date_sent_last:
                # Selected Invitation has never been sent yet.
                leading_invitation = self.instance
                deprecated_invitation = selected_invitation
            elif not self.instance.date_sent_last:
                # Instance has never been sent yet.
                leading_invitation = selected_invitation
                deprecated_invitation = self.instance
            elif selected_invitation.date_sent_last > self.instance.date_sent_last:
                # Lastest reminder: selected Invitation
                leading_invitation = selected_invitation
                deprecated_invitation = self.instance
            else:
                # Lastest reminder: instance
                leading_invitation = self.instance
                deprecated_invitation = selected_invitation

            # Move CitationNotification to the new leading Invitation
            deprecated_invitation.citation_notifications.update(invitation=leading_invitation)
            leading_invitation.times_sent += deprecated_invitation.times_sent   # Update counts
            leading_invitation.save()

            qs_contributor = deprecated_invitation.citation_notifications.filter(
                contributor__isnull=False).values_list('contributor', flat=True)
            if qs_contributor:
                if not leading_invitation.citation_notifications.filter(contributor__isnull=False):
                    # Contributor is already assigned in "old" RegistrationInvitation, copy it.
                    leading_invitation.citation_notifications.filter(contributor=qs_contributor[0])

            # Magic.
            deprecated_invitation.delete()
        return self.instance


class RegistrationInvitationForm(AcceptRequestMixin, forms.ModelForm):
    cited_in_submissions = forms.ModelMultipleChoiceField(
        queryset=Submission.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='/submissions/submission-autocomplete',
            attrs={'data-html': True}
        ),
        required=False
    )
    cited_in_publications = forms.ModelMultipleChoiceField(
        queryset=Publication.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='/journals/publication-autocomplete',
            attrs={'data-html': True}
        ),
        required=False
    )

    class Meta:
        model = RegistrationInvitation
        fields = (
            'profile',
            'title',
            'first_name',
            'last_name',
            'email',
            'message_style',
            'invitation_type',
            'personal_message')
        widgets = {
            'profile': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        # Find Submissions/Publications related to the invitation and fill the autocomplete fields
        initial = kwargs.get('initial', {})
        invitation = kwargs.get('instance', None)
        if invitation:
            submission_ids = invitation.citation_notifications.for_submissions().values_list(
                'submission_id', flat=True)
            publication_ids = invitation.citation_notifications.for_publications().values_list(
                'publication_id', flat=True)
            initial['cited_in_submissions'] = Submission.objects.filter(id__in=submission_ids)
            initial['cited_in_publications'] = Publication.objects.filter(id__in=publication_ids)
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        if not self.request.user.has_perm('scipost.can_manage_registration_invitations'):
            del self.fields['message_style']
            del self.fields['personal_message']
        if not self.request.user.has_perm('scipost.can_invite_fellows'):
            del self.fields['invitation_type']  # Only admins can invite fellows

    def clean_email(self):
        email = self.cleaned_data['email']
        if Contributor.objects.filter(user__email=email).exists():
            self.add_error('email', 'This email address is already associated to a Contributor')
        elif RegistrationInvitation.objects.declined().filter(email=email).exists():
            self.add_error('email', 'This person has already declined an earlier invitation')

        return email

    def save(self, *args, **kwargs):
        if not hasattr(self.instance, 'created_by'):
            self.instance.created_by = self.request.user
        if not hasattr(self.instance, 'invited_by'):
            self.instance.invited_by = self.request.user

        # Try to associate an existing Profile to invitation:
        profile = Profile.objects.get_unique_from_email_or_None(
            email=self.cleaned_data['email'])
        self.instance.profile = profile

        invitation = super().save(*args, **kwargs)
        if kwargs.get('commit', True):
            # Save the Submission notifications
            submissions = Submission.objects.filter(
                id__in=self.cleaned_data['cited_in_submissions'])
            for submission in submissions:
                CitationNotification.objects.get_or_create(
                    invitation=self.instance,
                    submission=submission,
                    defaults={
                        'created_by': self.instance.created_by
                    })

            # Save the Publication notifications
            publications = Publication.objects.filter(
                id__in=self.cleaned_data['cited_in_publications'])
            for publication in publications:
                CitationNotification.objects.get_or_create(
                    invitation=self.instance,
                    publication=publication,
                    defaults={
                        'created_by': self.instance.created_by
                    })
        return invitation


class RegistrationInvitationReminderForm(AcceptRequestMixin, forms.ModelForm):
    class Meta:
        model = RegistrationInvitation
        fields = ()

    def save(self, *args, **kwargs):
        if kwargs.get('commit', True):
            self.instance.mail_sent()
        return super().save(*args, **kwargs)


class RegistrationInvitationMapToContributorForm(AcceptRequestMixin, forms.ModelForm):
    contributor = None

    class Meta:
        model = RegistrationInvitation
        fields = ()

    def clean(self, *args, **kwargs):
        try:
            self.contributor = Contributor.objects.get(
                id=self.request.resolver_match.kwargs['contributor_id'])
        except Contributor.DoesNotExist:
            self.add_error(None, 'Contributor does not exist.')
        return {}

    def get_contributor(self):
        if not self.contributor:
            self.clean()
        return self.contributor

    def save(self, *args, **kwargs):
        if kwargs.get('commit', True):
            self.instance.citation_notifications.update(contributor=self.contributor)
            self.instance.delete()
        return self.instance


class RegistrationInvitationMarkForm(AcceptRequestMixin, forms.ModelForm):
    class Meta:
        model = RegistrationInvitation
        fields = ()

    def save(self, *args, **kwargs):
        if kwargs.get('commit', True):
            self.instance.mail_sent()
        return self.instance
