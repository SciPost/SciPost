__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.db.models import QuerySet

from crispy_forms.layout import Layout, Div
from crispy_bootstrap5.bootstrap5 import FloatingField

from common.forms import CrispyFormMixin, SearchForm
from mails.utils import DirectMailUtil
from scipost.models import Contributor
from common.utils import get_current_domain

from .models import ThesisLink


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
            "defense_date": forms.DateInput(attrs={"type": "date"}),
            "pub_link": forms.TextInput(attrs={"placeholder": "Full URL"}),
        }


class RequestThesisLinkForm(BaseRequestThesisLinkForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.user = self.request.user
        super(RequestThesisLinkForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Prefill instance before save"""
        self.instance.requested_by = Contributor.objects.get(dbuser=self.user)
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

    def vet_request(self, thesislink: ThesisLink, user):
        mail_context = {
            "thesislink": thesislink,
            "domain": get_current_domain(),
        }
        match action_id := int(self.cleaned_data["action_option"]):
            case self.ACCEPT:
                mail_code = "theses/thesislink_vetting_accepted"
                thesislink.vetted = True
                thesislink.vetted_by = user.contributor
            case self.MODIFY:
                mail_code = "theses/thesislink_vetting_modified"
                thesislink.vetted = True
                thesislink.vetted_by = user.contributor
            case self.REFUSE:
                mail_code = "theses/thesislink_vetting_rejected"
                refusal_reason = dict(self.fields["refusal_reason"].choices)[
                    int(self.cleaned_data["refusal_reason"])
                ]
                justification = self.cleaned_data["justification"]
                mail_context.update(
                    {
                        "refusal_reason": refusal_reason,
                        "justification": justification,
                    }
                )
            case _:
                raise ValueError("Invalid action option selected")

        DirectMailUtil(
            mail_code,
            **mail_context,
        ).send_mail()

        if action_id == self.REFUSE:
            thesislink.delete()


class ThesisLinkSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(
        max_length=1000, required=False, label="Abstract"
    )
    supervisor = forms.CharField(max_length=100, required=False, label="Supervisor")


class ThesisSearchForm(CrispyFormMixin, SearchForm[ThesisLink]):
    model = ThesisLink
    queryset = ThesisLink.objects.vetted()

    author = forms.CharField(max_length=100, required=False, label="Author")
    title = forms.CharField(max_length=100, label="Title", required=False)
    abstract = forms.CharField(max_length=1000, required=False, label="Abstract")
    supervisor = forms.CharField(max_length=100, required=False, label="Supervisor")

    def __init__(self, *args, **kwargs):
        self.acad_field_slug = kwargs.pop("acad_field_slug")
        self.specialty_slug = kwargs.pop("specialty_slug")
        super().__init__(*args, **kwargs)

    def get_form_layout(self) -> Layout:
        return Layout(
            Div(
                Div(FloatingField("author"), css_class="col-12 col-md-6"),
                Div(FloatingField("title"), css_class="col-12 col-md-6"),
                Div(FloatingField("abstract"), css_class="col-12 col-md-6"),
                Div(FloatingField("supervisor"), css_class="col-12 col-md-6"),
                css_class="row",
            ),
        )

    def filter_queryset(self, queryset: "QuerySet[ThesisLink]"):
        """Return all ThesisLink objects fitting search"""
        if self.acad_field_slug and self.acad_field_slug != "all":
            queryset = queryset.filter(acad_field__slug=self.acad_field_slug)
        if self.specialty_slug and self.specialty_slug != "all":
            queryset = queryset.filter(specialties__slug=self.specialty_slug)
        if title := self.cleaned_data.get("title"):
            queryset = queryset.filter(title__icontains=title)
        if abstract := self.cleaned_data.get("abstract"):
            queryset = queryset.filter(abstract__icontains=abstract)
        if author := self.cleaned_data.get("author"):
            queryset = queryset.filter(author__icontains=author)
        if supervisor := self.cleaned_data.get("supervisor"):
            queryset = queryset.filter(supervisor__icontains=supervisor)
        return queryset.order_by("-defense_date")
