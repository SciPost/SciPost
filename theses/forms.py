__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from scipost.models import Contributor
from scipost.utils import build_absolute_uri_using_site

from .models import ThesisLink
from .helpers import past_years


class BaseRequestThesisLinkForm(forms.ModelForm):
    class Meta:
        model = ThesisLink
        fields = ['type', 'discipline', 'subject_area', 'approaches',
                  'title', 'author', 'supervisor', 'institution',
                  'defense_date', 'pub_link', 'abstract']
        widgets = {
            'defense_date': forms.SelectDateWidget(years=past_years(50)),
            'pub_link': forms.TextInput(attrs={'placeholder': 'Full URL'})
        }


class RequestThesisLinkForm(BaseRequestThesisLinkForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.user = self.request.user
        super(RequestThesisLinkForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Prefill instance before save"""
        self.instance.requested_by = Contributor.objects.get(user=self.user)
        return super(RequestThesisLinkForm, self).save(*args, **kwargs)


class VetThesisLinkForm(BaseRequestThesisLinkForm):
    MODIFY = 0
    ACCEPT = 1
    REFUSE = 2
    THESIS_ACTION_CHOICES = (
        (MODIFY, 'modify'),
        (ACCEPT, 'accept'),
        (REFUSE, 'refuse (give reason below)'),
    )

    EMPTY_CHOICE = 0
    ALREADY_EXISTS = 1
    LINK_DOES_NOT_WORK = 2
    THESIS_REFUSAL_CHOICES = (
        (EMPTY_CHOICE, '---'),
        (ALREADY_EXISTS, 'A link to this thesis already exists'),
        (LINK_DOES_NOT_WORK, 'The external link to this thesis does not work'),
    )

    action_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=THESIS_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=THESIS_REFUSAL_CHOICES, required=False)
    justification = forms.CharField(widget=forms.Textarea(
        attrs={'rows': 5, 'cols': 40}), label='Justification (optional)', required=False)

    def __init__(self, *args, **kwargs):
        super(VetThesisLinkForm, self).__init__(*args, **kwargs)
        self.order_fields(['action_option', 'refusal_reason', 'justification'])

    def vet_request(self, thesislink, user):
        mail_params = {
            'vocative_title': thesislink.requested_by.get_title_display(),
            'thesislink': thesislink,
            'full_url': build_absolute_uri_using_site(thesislink.get_absolute_url())
        }
        action = int(self.cleaned_data['action_option'])

        if action == VetThesisLinkForm.ACCEPT or action == VetThesisLinkForm.MODIFY:
            thesislink.vetted = True
            thesislink.vetted_by = Contributor.objects.get(user=user)
            thesislink.save()

            subject_line = 'SciPost Thesis Link activated'
            if action == VetThesisLinkForm.ACCEPT:
                message_plain = render_to_string('theses/thesislink_accepted.txt', mail_params)
            elif action == VetThesisLinkForm.MODIFY:
                message_plain = render_to_string('theses/thesislink_modified.txt', mail_params)

        elif action == VetThesisLinkForm.REFUSE:
            refusal_reason = int(self.cleaned_data['refusal_reason'])
            refusal_reason = dict(self.fields['refusal_reason'].choices)[refusal_reason]
            mail_params['refusal_reason'] = refusal_reason
            mail_params['justification'] = self.cleaned_data['justification']

            message_plain = render_to_string('theses/thesislink_refused.txt', mail_params)
            subject_line = 'SciPost Thesis Link'

            thesislink.delete()

        email = EmailMessage(
            subject_line,
            message_plain,
            'SciPost Theses <theses@scipost.org>',
            [thesislink.requested_by.user.email],
            ['theses@scipost.org'],
            reply_to=['theses@scipost.org']
        ).send(fail_silently=False)


class ThesisLinkSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")
    supervisor = forms.CharField(max_length=100, required=False, label="Supervisor")
