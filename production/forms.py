import datetime

from django import forms
from django.utils.dates import MONTHS
from django.db.models import Sum

from . import constants
from .models import ProductionUser, ProductionStream, ProductionEvent, Proof
from .signals import notify_stream_status_change

today = datetime.datetime.today()


class ProductionEventForm(forms.ModelForm):
    class Meta:
        model = ProductionEvent
        fields = (
            'comments',
            'duration'
        )
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
            'duration': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'})
        }


class AssignOfficerForm(forms.ModelForm):
    class Meta:
        model = ProductionStream
        fields = ('officer',)

    def save(self, commit=True):
        stream = super().save(False)
        if commit:
            if stream.status == constants.PRODUCTION_STREAM_INITIATED:
                stream.status = constants.PROOFS_TASKED
            stream.save()
        return stream


class AssignSupervisorForm(forms.ModelForm):
    class Meta:
        model = ProductionStream
        fields = ('supervisor',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supervisor'].queryset = self.fields['supervisor'].queryset.filter(
            user__groups__name='Production Supervisor')


class StreamStatusForm(forms.ModelForm):
    class Meta:
        model = ProductionStream
        fields = ('status',)

    def __init__(self, *args, **kwargs):
        self.current_production_user = kwargs.pop('production_user')
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = self.get_available_statuses()

    def get_available_statuses(self):
        if self.instance.status in [constants.PRODUCTION_STREAM_INITIATED,
                                    constants.PRODUCTION_STREAM_COMPLETED,
                                    constants.PROOFS_ACCEPTED,
                                    constants.PROOFS_CITED]:
            # No status change can be made by User
            return ()
        elif self.instance.status == constants.PROOFS_TASKED:
            return (
                (constants.PROOFS_PRODUCED, 'Proofs have been produced'),
            )
        elif self.instance.status == constants.PROOFS_PRODUCED:
            return (
                (constants.PROOFS_CHECKED, 'Proofs have been checked by Supervisor'),
                (constants.PROOFS_SENT, 'Proofs sent to Authors'),
            )
        elif self.instance.status == constants.PROOFS_CHECKED:
            return (
                (constants.PROOFS_SENT, 'Proofs sent to Authors'),
                (constants.PROOFS_CORRECTED, 'Corrections implemented'),
            )
        elif self.instance.status == constants.PROOFS_SENT:
            return (
                (constants.PROOFS_RETURNED, 'Proofs returned by Authors'),
                (constants.PROOFS_ACCEPTED, 'Authors have accepted proofs'),
            )
        elif self.instance.status == constants.PROOFS_RETURNED:
            return (
                (constants.PROOFS_CHECKED, 'Proofs have been checked by Supervisor'),
                (constants.PROOFS_SENT, 'Proofs sent to Authors'),
                (constants.PROOFS_CORRECTED, 'Corrections implemented'),
                (constants.PROOFS_ACCEPTED, 'Authors have accepted proofs'),
            )
        elif self.instance.status == constants.PROOFS_CORRECTED:
            return (
                (constants.PROOFS_CHECKED, 'Proofs have been checked by Supervisor'),
                (constants.PROOFS_SENT, 'Proofs sent to Authors'),
                (constants.PROOFS_ACCEPTED, 'Authors have accepted proofs'),
            )
        elif self.instance.status == constants.PROOFS_PUBLISHED:
            return (
                (constants.PROOFS_CITED, 'Cited people have been notified/invited to SciPost'),
            )
        return ()

    def save(self, commit=True):
        stream = super().save(commit)
        if commit:
            event = ProductionEvent(
                stream=stream,
                event='status',
                comments='Stream changed status to: {status}'.format(
                    status=stream.get_status_display()),
                noted_by=self.current_production_user)
            event.save()
            notify_stream_status_change(sender=self.current_production_user.user, instance=stream,
                                        created=False)
        return stream


class UserToOfficerForm(forms.ModelForm):
    class Meta:
        model = ProductionUser
        fields = (
            'user',
        )


class ProductionUserMonthlyActiveFilter(forms.Form):
    month = forms.ChoiceField(choices=[(k, v) for k, v in MONTHS.items()])
    year = forms.ChoiceField(choices=[(y, y) for y in reversed(range(today.year-6, today.year+1))])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['month'].initial = today.month
        self.fields['year'].initial = today.year

    def get_totals(self):
        users = ProductionUser.objects.filter(events__duration__isnull=False,
                                              events__noted_on__month=self.cleaned_data['month'],
                                              events__noted_on__year=self.cleaned_data['year']
                                              ).distinct()
        output = []
        for user in users:
            events = user.events.filter(duration__isnull=False,
                                        noted_on__month=self.cleaned_data['month'],
                                        noted_on__year=self.cleaned_data['year'])
            output.append({
                'events': events,
                'duration': events.aggregate(total=Sum('duration')),
                'user': user
            })

        return output


class ProofUploadForm(forms.ModelForm):
    class Meta:
        model = Proof
        fields = ('attachment',)
