from django import forms
from django.contrib import messages

from journals.models import Publication
from scipost.models import Contributor
from submissions.models import Submission

from . import constants
from .models import RegistrationInvitation, CitationNotification

from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField


class AcceptRequestMixin:
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)


class RegistrationInvitationFilterForm(forms.Form):
    last_name = forms.CharField()

    def search(self, qs):
        last_name = self.cleaned_data.get('last_name')
        return qs.filter(last_name__icontains=last_name)


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
    submission = AutoCompleteSelectField('submissions_lookup', required=False)
    publication = AutoCompleteSelectField('publication_lookup', required=False)

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
    cited_in_submissions = AutoCompleteSelectMultipleField('submissions_lookup', required=False)
    cited_in_publications = AutoCompleteSelectMultipleField('publication_lookup', required=False)

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


class RegistrationInvitationForm(AcceptRequestMixin, forms.ModelForm):
    cited_in_submissions = AutoCompleteSelectMultipleField('submissions_lookup', required=False)
    cited_in_publications = AutoCompleteSelectMultipleField('publication_lookup', required=False)

    class Meta:
        model = RegistrationInvitation
        fields = (
            'title',
            'first_name',
            'last_name',
            'email',
            'message_style',
            'personal_message')

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
