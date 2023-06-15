__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.db.models.functions import Greatest

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField
from django.urls import reverse

from journals.models import Journal
from markup.widgets import TextareaWithPreview
from proceedings.models import Proceedings
from proceedings.forms import ProceedingsMultipleChoiceField
from scipost.fields import UserModelChoiceField

from . import constants
from .models import (
    ProductionUser,
    ProductionStream,
    ProductionEvent,
    Proofs,
    ProductionEventAttachment,
)


today = datetime.datetime.today()


class ProductionEventForm(forms.ModelForm):
    class Meta:
        model = ProductionEvent
        fields = (
            "stream",
            "comments",
            "noted_by",
        )
        widgets = {
            "comments": TextareaWithPreview(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("stream", type="hidden"),
            Field("comments"),
            Field("noted_by", type="hidden"),
            Submit("submit", "Submit"),
        )


class ProductionEventForm_deprec(forms.ModelForm):
    class Meta:
        model = ProductionEvent
        fields = ("comments",)
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 4}),
        }


class AssignOfficerForm(forms.ModelForm):
    class Meta:
        model = ProductionStream
        fields = ("officer",)

    def save(self, commit=True):
        stream = super().save(False)
        if commit:
            if stream.status in [
                constants.PRODUCTION_STREAM_INITIATED,
                constants.PROOFS_SOURCE_REQUESTED,
            ]:
                stream.status = constants.PROOFS_TASKED
            stream.save()
        return stream


class AssignInvitationsOfficerForm(forms.ModelForm):
    class Meta:
        model = ProductionStream
        fields = ("invitations_officer",)


class AssignSupervisorForm(forms.ModelForm):
    class Meta:
        model = ProductionStream
        fields = ("supervisor",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supervisor"].queryset = self.fields["supervisor"].queryset.filter(
            user__groups__name="Production Supervisor"
        )


class StreamStatusForm(forms.ModelForm):
    class Meta:
        model = ProductionStream
        fields = ("status",)

    def __init__(self, *args, **kwargs):
        self.current_production_user = kwargs.pop("production_user")
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = self.get_available_statuses()

    def get_available_statuses(self):
        if self.instance.status in [
            constants.PRODUCTION_STREAM_COMPLETED,
            constants.PROOFS_SOURCE_REQUESTED,
            constants.PROOFS_ACCEPTED,
            constants.PROOFS_CITED,
        ]:
            # No status change can be made by User
            return ()
        elif self.instance.status == constants.PRODUCTION_STREAM_INITIATED:
            return ((constants.PROOFS_SOURCE_REQUESTED, "Source files requested"),)
        elif self.instance.status == constants.PROOFS_TASKED:
            return ((constants.PROOFS_PRODUCED, "Proofs have been produced"),)
        elif self.instance.status == constants.PROOFS_PRODUCED:
            return (
                (constants.PROOFS_CHECKED, "Proofs have been checked by Supervisor"),
                (constants.PROOFS_SENT, "Proofs sent to Authors"),
            )
        elif self.instance.status == constants.PROOFS_CHECKED:
            return (
                (constants.PROOFS_SENT, "Proofs sent to Authors"),
                (constants.PROOFS_CORRECTED, "Corrections implemented"),
                (constants.PROOFS_SOURCE_REQUESTED, "Source files requested"),
            )
        elif self.instance.status == constants.PROOFS_SENT:
            return (
                (constants.PROOFS_RETURNED, "Proofs returned by Authors"),
                (constants.PROOFS_ACCEPTED, "Authors have accepted proofs"),
            )
        elif self.instance.status == constants.PROOFS_RETURNED:
            return (
                (constants.PROOFS_CHECKED, "Proofs have been checked by Supervisor"),
                (constants.PROOFS_SENT, "Proofs sent to Authors"),
                (constants.PROOFS_CORRECTED, "Corrections implemented"),
                (constants.PROOFS_ACCEPTED, "Authors have accepted proofs"),
            )
        elif self.instance.status == constants.PROOFS_CORRECTED:
            return (
                (constants.PROOFS_CHECKED, "Proofs have been checked by Supervisor"),
                (constants.PROOFS_SENT, "Proofs sent to Authors"),
                (constants.PROOFS_ACCEPTED, "Authors have accepted proofs"),
            )
        elif self.instance.status == constants.PROOFS_PUBLISHED:
            return (
                (
                    constants.PROOFS_CITED,
                    "Cited people have been notified/invited to SciPost",
                ),
            )
        return ()

    def save(self, commit=True):
        stream = super().save(commit)
        if commit:
            event = ProductionEvent(
                stream=stream,
                event="status",
                comments="Stream changed status to: {status}".format(
                    status=stream.get_status_display()
                ),
                noted_by=self.current_production_user,
            )
            event.save()
        return stream


class UserToOfficerForm(forms.ModelForm):
    user = UserModelChoiceField(
        queryset=get_user_model()
        .objects.filter(production_user__isnull=True)
        .order_by("last_name"),
        required=False,
    )

    class Meta:
        model = ProductionUser
        fields = ("user",)

    def save(self, commit=True):
        if user := self.cleaned_data["user"]:
            existing_production_user = ProductionUser.objects.filter(
                name=f"{user.first_name} {user.last_name}"
            ).first()
            if existing_production_user:
                existing_production_user.user = user
                existing_production_user.save()

            else:
                production_user = ProductionUser.objects.create(
                    name=f"{user.first_name} {user.last_name}", user=user
                )
                production_user.save()


class ProofsUploadForm(forms.ModelForm):
    class Meta:
        model = Proofs
        fields = ("attachment",)


class ProofsDecisionForm(forms.ModelForm):
    decision = forms.ChoiceField(
        choices=[
            (True, "Accept Proofs for publication"),
            (False, "Decline Proofs for publication"),
        ]
    )
    feedback = forms.CharField(required=False, widget=forms.Textarea)
    feedback_attachment = forms.FileField(required=False)

    class Meta:
        model = Proofs
        fields = ()

    def save(self, commit=True):
        proofs = self.instance
        decision = self.cleaned_data["decision"]
        comments = self.cleaned_data["feedback"]

        if decision in ["True", True]:
            proofs.status = constants.PROOFS_ACCEPTED
            if proofs.stream.status in [
                constants.PROOFS_PRODUCED,
                constants.PROOFS_CHECKED,
                constants.PROOFS_SENT,
                constants.PROOFS_CORRECTED,
            ]:
                # Force status change on Stream if appropriate
                proofs.stream.status = constants.PROOFS_ACCEPTED
        else:
            proofs.status = constants.PROOFS_DECLINED
            proofs.stream.status = constants.PROOFS_RETURNED

        if commit:
            proofs.save()
            proofs.stream.save()

            prodevent = ProductionEvent(
                stream=proofs.stream,
                event="status",
                comments="<em>Received feedback from the authors:</em><br>{comments}".format(
                    comments=comments
                ),
                noted_by=proofs.stream.supervisor,
            )
            prodevent.save()
            if self.cleaned_data.get("feedback_attachment"):
                attachment = ProductionEventAttachment(
                    attachment=self.cleaned_data["feedback_attachment"],
                    production_event=prodevent,
                )
                attachment.save()
        return proofs


class ProductionStreamSearchForm(forms.Form):
    accepted_in = forms.ModelMultipleChoiceField(
        queryset=Journal.objects.active(),
        required=False,
    )
    proceedings = ProceedingsMultipleChoiceField(
        queryset=Proceedings.objects.order_by("-submissions_close"),
        required=False,
    )
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=512, required=False)
    identifier = forms.CharField(max_length=128, required=False)
    officer = forms.ModelChoiceField(
        queryset=ProductionUser.objects.active(),
        required=False,
        empty_label="Any",
    )
    supervisor = forms.ModelChoiceField(
        queryset=ProductionUser.objects.active(),
        required=False,
        empty_label="Any",
    )
    status = forms.MultipleChoiceField(
        # Use short status names from their internal (code) name
        choices=[
            (status_code_name, status_code_name.replace("_", " ").title())
            for status_code_name, _ in constants.PRODUCTION_STREAM_STATUS
        ],
        required=False,
    )
    orderby = forms.ChoiceField(
        label="Order by",
        choices=(
            ("submission__editorial_decision__taken_on", "Date accepted"),
            ("latest_activity_annot", "Latest activity"),
            (
                "status,submission__editorial_decision__taken_on",
                "Status + Date accepted",
            ),
            ("status,latest_activity_annot", "Status + Latest activity"),
        ),
        required=False,
    )
    ordering = forms.ChoiceField(
        label="Ordering",
        choices=(
            # FIXME: Emperically, the ordering appers to be reversed for dates?
            ("-", "Ascending"),
            ("+", "Descending"),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(FloatingField("identifier"), css_class="col-md-3 col-4"),
                Div(FloatingField("author"), css_class="col-md-3 col-8"),
                Div(FloatingField("title"), css_class="col-md-6"),
                css_class="row mb-0 mt-2",
            ),
            Div(
                Div(
                    Div(
                        Div(Field("accepted_in", size=3), css_class="col-sm-8"),
                        Div(Field("proceedings", size=3), css_class="col-sm-4"),
                        css_class="row mb-0",
                    ),
                    Div(
                        Div(Field("supervisor"), css_class="col-6"),
                        Div(Field("officer"), css_class="col-6"),
                        css_class="row mb-0",
                    ),
                    Div(
                        Div(Field("orderby"), css_class="col-6"),
                        Div(Field("ordering"), css_class="col-6"),
                        css_class="row mb-0",
                    ),
                    css_class="col-sm-9",
                ),
                Div(
                    Field("status", size=len(constants.PRODUCTION_STREAM_STATUS)),
                    css_class="col-sm-3",
                ),
                css_class="row mb-0",
            ),
        )

    def search_results(self):
        streams = ProductionStream.objects.ongoing()

        streams = streams.annotate(
            latest_activity_annot=Greatest(Max("events__noted_on"), "opened", "closed")
        )

        if accepted_in := self.cleaned_data.get("accepted_in"):
            streams = streams.filter(
                submission__editorialdecision__for_journal__in=accepted_in,
            )
        if proceedings := self.cleaned_data.get("proceedings"):
            streams = streams.filter(submission__proceedings__in=proceedings)

        if identifier := self.cleaned_data.get("identifier"):
            streams = streams.filter(
                submission__preprint__identifier_w_vn_nr__icontains=identifier,
            )
        if author := self.cleaned_data.get("author"):
            streams = streams.filter(submission__author_list__icontains=author)
        if title := self.cleaned_data.get("title"):
            streams = streams.filter(submission__title__icontains=title)

        if officer := self.cleaned_data.get("officer"):
            streams = streams.filter(officer=officer)
        if supervisor := self.cleaned_data.get("supervisor"):
            streams = streams.filter(supervisor=supervisor)
        if status := self.cleaned_data.get("status"):
            streams = streams.filter(status__in=status)

        if not self.user.has_perm("scipost.can_view_all_production_streams"):
            # Restrict stream queryset if user is not supervisor
            streams = streams.filter_for_user(self.user.production_user)

        # Ordering of streams
        # Only order if both fields are set
        if (orderby_value := self.cleaned_data.get("orderby")) and (
            ordering_value := self.cleaned_data.get("ordering")
        ):
            # Remove the + from the ordering value, causes a Django error
            ordering_value = ordering_value.replace("+", "")

            # Ordering string is built by the ordering (+/-), and the field name
            # from the orderby field split by "," and joined together
            streams = streams.order_by(
                *[
                    ordering_value + order_part
                    for order_part in orderby_value.split(",")
                ]
            )

        return streams


class BulkAssignOfficersForm(forms.Form):
    officer = forms.ModelChoiceField(
        queryset=ProductionUser.objects.active().filter(
            user__groups__name="Production Officers"
        ),
        required=False,
        empty_label="Unchanged",
    )
    supervisor = forms.ModelChoiceField(
        queryset=ProductionUser.objects.active().filter(
            user__groups__name="Production Supervisor"
        ),
        required=False,
        empty_label="Unchanged",
    )

    def __init__(self, *args, **kwargs):
        self.productionstreams = kwargs.pop("productionstreams", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "productionstreams-bulk-action-form"
        self.helper.attrs = {
            "hx-post": reverse(
                "production:_hx_productionstream_actions_bulk_assign_officers"
            ),
            "hx-target": "#productionstream-bulk-assign-officers-container",
            "hx-swap": "outerHTML",
            "hx-confirm": "Are you sure you want to assign the selected production streams to the selected officers?",
        }
        self.helper.layout = Layout(
            Div(
                Div(Field("supervisor"), css_class="col-6 col-md-4 col-lg-3"),
                Div(Field("officer"), css_class="col-6 col-md-4 col-lg-3"),
                css_class="row mb-0",
            ),
        )
