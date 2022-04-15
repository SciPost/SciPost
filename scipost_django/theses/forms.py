__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div
from crispy_bootstrap5.bootstrap5 import FloatingField

from scipost.models import Contributor
from scipost.utils import build_absolute_uri_using_site
from common.utils import get_current_domain

from .models import ThesisLink
from .helpers import past_years


class BaseRequestThesisLinkForm(forms.ModelForm):
    class Meta:
        model = ThesisLink
        fields = [
            "type",
            "acad_field",
            "specialties",
            "approaches",
            "title",
            "author",
            "supervisor",
            "institution",
            "defense_date",
            "pub_link",
            "abstract",
        ]
        widgets = {
            "defense_date": forms.SelectDateWidget(years=past_years(50)),
            "pub_link": forms.TextInput(attrs={"placeholder": "Full URL"}),
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
        (MODIFY, "modify"),
        (ACCEPT, "accept"),
        (REFUSE, "refuse (give reason below)"),
    )

    EMPTY_CHOICE = 0
    ALREADY_EXISTS = 1
    LINK_DOES_NOT_WORK = 2
    THESIS_REFUSAL_CHOICES = (
        (EMPTY_CHOICE, "---"),
        (ALREADY_EXISTS, "A link to this thesis already exists"),
        (LINK_DOES_NOT_WORK, "The external link to this thesis does not work"),
    )

    action_option = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=THESIS_ACTION_CHOICES,
        required=True,
        label="Action",
    )
    refusal_reason = forms.ChoiceField(choices=THESIS_REFUSAL_CHOICES, required=False)
    justification = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5, "cols": 40}),
        label="Justification (optional)",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(VetThesisLinkForm, self).__init__(*args, **kwargs)
        self.order_fields(["action_option", "refusal_reason", "justification"])

    def vet_request(self, thesislink, user):
        mail_params = {
            "vocative_title": thesislink.requested_by.profile.get_title_display(),
            "thesislink": thesislink,
            "full_url": build_absolute_uri_using_site(thesislink.get_absolute_url()),
        }
        action = int(self.cleaned_data["action_option"])

        if action == VetThesisLinkForm.ACCEPT or action == VetThesisLinkForm.MODIFY:
            thesislink.vetted = True
            thesislink.vetted_by = Contributor.objects.get(user=user)
            thesislink.save()

            subject_line = "SciPost Thesis Link activated"
            if action == VetThesisLinkForm.ACCEPT:
                message_plain = render_to_string(
                    "theses/thesislink_accepted.txt", mail_params
                )
            elif action == VetThesisLinkForm.MODIFY:
                message_plain = render_to_string(
                    "theses/thesislink_modified.txt", mail_params
                )

        elif action == VetThesisLinkForm.REFUSE:
            refusal_reason = int(self.cleaned_data["refusal_reason"])
            refusal_reason = dict(self.fields["refusal_reason"].choices)[refusal_reason]
            mail_params["refusal_reason"] = refusal_reason
            mail_params["justification"] = self.cleaned_data["justification"]

            message_plain = render_to_string(
                "theses/thesislink_refused.txt", mail_params
            )
            subject_line = "SciPost Thesis Link"

            thesislink.delete()

        domain = get_current_domain()
        email = EmailMessage(
            subject_line,
            message_plain,
            f"SciPost Theses <theses@{domain}>",
            [thesislink.requested_by.user.email],
            [f"theses@{domain}"],
            reply_to=[f"theses@{domain}"],
        ).send(fail_silently=False)


class ThesisLinkSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(
        max_length=1000, required=False, label="Abstract"
    )
    supervisor = forms.CharField(max_length=100, required=False, label="Supervisor")


class ThesisSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author")
    title = forms.CharField(max_length=100, label="Title", required=False)
    abstract = forms.CharField(
        max_length=1000, required=False, label="Abstract"
    )
    supervisor = forms.CharField(max_length=100, required=False, label="Supervisor")

    def __init__(self, *args, **kwargs):
        self.acad_field_slug = kwargs.pop("acad_field_slug")
        self.specialty_slug = kwargs.pop("specialty_slug")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                FloatingField("author"),
                FloatingField("title"),
                FloatingField("abstract"),
                FloatingField("supervisor"),
            ),
        )

    def search_results(self):
        """Return all ThesisLink objects fitting search"""
        theses = ThesisLink.objects.vetted()
        if self.acad_field_slug and self.acad_field_slug != "all":
            theses = theses.filter(acad_field__slug=self.acad_field_slug)
            if self.specialty_slug and self.specialty_slug != "all":
                theses = theses.filter(
                    specialties__slug=self.specialty_slug
                )
        if hasattr(self, "cleaned_data"):
            if "title" in self.cleaned_data:
                theses = theses.filter(
                    title__icontains=self.cleaned_data["title"],
                )
                len(theses)
            if "abstract" in self.cleaned_data:
                theses = theses.filter(
                    abstract__icontains=self.cleaned_data["abstract"],
                )
            if "author" in self.cleaned_data:
                theses = theses.filter(
                    author__icontains=self.cleaned_data["author"],
                )
            if "supervisor" in self.cleaned_data:
                theses = theses.filter(
                    supervisor__icontains=self.cleaned_data["supervisor"],
                )
        return theses.order_by("-defense_date")
