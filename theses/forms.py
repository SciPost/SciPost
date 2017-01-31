from django import forms
from django.core.mail import EmailMessage

from .models import *
from .helpers import past_years


class RequestThesisLinkForm(forms.ModelForm):
    class Meta:
        model = ThesisLink
        fields = ['type', 'discipline', 'domain', 'subject_area',
                  'title', 'author', 'supervisor', 'institution',
                  'defense_date', 'pub_link', 'abstract']
        widgets = {
            'defense_date': forms.SelectDateWidget(years=past_years(50)),
            'pub_link': forms.TextInput(attrs={'placeholder': 'Full URL'})
        }


class VetThesisLinkForm(RequestThesisLinkForm):
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
        (ALREADY_EXISTS, 'a link to this thesis already exists'),
        (LINK_DOES_NOT_WORK, 'the external link to this thesis does not work'),
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
        if int(self.cleaned_data['action_option']) == VetThesisLinkForm.ACCEPT:
            thesislink.vetted = True
            thesislink.vetted_by = Contributor.objects.get(user=user)
            thesislink.save()

            email_text = ('Dear ' + title_dict[thesislink.requested_by.title] + ' '
                          + thesislink.requested_by.user.last_name
                          + ', \n\nThe Thesis Link you have requested, concerning thesis with title '
                          + thesislink.title + ' by ' + thesislink.author
                          + ', has been activated at https://scipost.org/thesis/'
                          + str(thesislink.id) + '.'
                          + '\n\nThank you for your contribution, \nThe SciPost Team.')
            emailmessage = EmailMessage('SciPost Thesis Link activated', email_text,
                                        'SciPost Theses <theses@scipost.org>',
                                        [thesislink.requested_by.user.email],
                                        ['theses@scipost.org'],
                                        reply_to=['theses@scipost.org'])
            emailmessage.send(fail_silently=False)
        elif int(self.cleaned_data['action_option']) == VetThesisLinkForm.REFUSE:
            email_text = ('Dear ' + title_dict[thesislink.requested_by.title] + ' '
                          + thesislink.requested_by.user.last_name
                          + ', \n\nThe Thesis Link you have requested, concerning thesis with title '
                          + thesislink.title + ' by ' + thesislink.author
                          + ', has not been activated for the following reason: '
                          + self.cleaned_data['refusal_reason']
                          + '.\n\nThank you for your interest, \nThe SciPost Team.')
            if self.cleaned_data['justification']:
                email_text += '\n\nFurther explanations: ' + \
                    self.cleaned_data['justification']
            emailmessage = EmailMessage('SciPost Thesis Link', email_text,
                                        'SciPost Theses <theses@scipost.org>',
                                        [thesislink.requested_by.user.email],
                                        ['theses@scipost.org'],
                                        reply_to=['theses@scipost.org'])
            emailmessage.send(fail_silently=False)
            thesislink.delete()

        elif int(self.cleaned_data['action_option']) == VetThesisLinkForm.MODIFY:
            thesislink.vetted = True
            thesislink.vetted_by = Contributor.objects.get(user=user)
            thesislink.save()
            email_text = ('Dear ' + title_dict[thesislink.requested_by.title] + ' '
                          + thesislink.requested_by.user.last_name
                          + ', \n\nThe Thesis Link you have requested, concerning thesis with title '
                          + thesislink.title + ' by ' + thesislink.author_list
                          + ', has been activated '
                          '(with slight modifications to your submitted details) at '
                          'https://scipost.org/thesis/' + str(thesislink.id) + '.'
                          '\n\nThank you for your contribution, \nThe SciPost Team.')
            emailmessage = EmailMessage('SciPost Thesis Link activated', email_text,
                                        'SciPost Theses <theses@scipost.org>',
                                        [thesislink.requested_by.user.email],
                                        ['theses@scipost.org'],
                                        reply_to=['theses@scipost.org'])
            emailmessage.send(fail_silently=False)


class ThesisLinkSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")
    supervisor = forms.CharField(max_length=100, required=False, label="Supervisor")
