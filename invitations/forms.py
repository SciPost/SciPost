from django import forms

from .models import RegistrationInvitation

from ajax_select.fields import AutoCompleteSelectMultipleField


class RegistrationInvitationForm(forms.ModelForm):
    cited_in_submission = AutoCompleteSelectMultipleField('submissions_lookup', required=False)
    cited_in_publication = AutoCompleteSelectMultipleField('publication_lookup', required=False)

    class Meta:
        model = RegistrationInvitation
        fields = (
            'title',
            'first_name',
            'last_name',
            'email',
            'message_style',
            'personal_message',
            'cited_in_submission',
            'cited_in_publication')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        if not self.request.user.has_perm('scipost.can_manage_registration_invitations'):
            del self.fields['message_style']
            del self.fields['personal_message']

    def save(self, *args, **kwargs):
        if not hasattr(self.instance, 'created_by'):
            self.instance.created_by = self.request.user
        return super().save(*args, **kwargs)


class RegistrationInvitationReminderForm(forms.ModelForm):
    class Meta:
        model = RegistrationInvitation
        fields = ()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.mail_sent()
        return super().save(*args, **kwargs)
