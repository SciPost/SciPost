__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django import forms
from django.contrib.auth import get_user_model

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
            if stream.status == constants.PRODUCTION_STREAM_INITIATED:
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
            constants.PRODUCTION_STREAM_INITIATED,
            constants.PRODUCTION_STREAM_COMPLETED,
            constants.PROOFS_ACCEPTED,
            constants.PROOFS_CITED,
        ]:
            # No status change can be made by User
            return ()
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
        .order_by("last_name")
    )

    class Meta:
        model = ProductionUser
        fields = ("user",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = (
            self.fields["user"]
            .queryset.filter(production_user__isnull=True)
            .order_by("last_name")
        )


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
