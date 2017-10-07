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
        )
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = self.fields['user'].queryset.filter(
            production_user__isnull=True).order_by('last_name')


class ProductionUserMonthlyActiveFilter(forms.Form):
    month = forms.ChoiceField(choices=[(k, v) for k, v in MONTHS.items()])
    year = forms.ChoiceField(choices=[(y, y) for y in reversed(range(today.year-6, today.year+1))])

    def __init__(self, *args, **kwargs):
        if not kwargs.get('data', False) and not args[0]:
            args = list(args)
            args[0] = {
                'month': today.month,
                'year': today.year
            }
            args = tuple(args)
        kwargs['initial'] = {
            'month': today.month,
            'year': today.year
        }
        super().__init__(*args, **kwargs)

    def get_totals(self):
        # Make accessible without need to explicitly check validity of form.
        self.is_valid()

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


class ProofDecisionForm(forms.ModelForm):
    decision = forms.ChoiceField(choices=[(True, 'Accept Proofs for publication'),
                                          (False, 'Decline Proofs for publication')])
    comments = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = Proof
        fields = ()

    def save(self, commit=True):
        proof = self.instance
        decision = self.cleaned_data['decision']
        comments = self.cleaned_data['comments']
        if decision:
            proof.status = constants.PROOF_ACCEPTED
            if proof.stream.status in [constants.PROOFS_PRODUCED,
                                       constants.PROOF_CHECKED,
                                       constants.PROOFS_SENT,
                                       constants.PROOFS_CORRECTED]:
                # Force status change on Stream if appropriate
                proof.stream.status = constants.PROOFS_ACCEPTED
        else:
            proof.status = constants.PROOF_DECLINED

        if commit:
            proof.save()
            proof.stream.save()

            prodevent = ProductionEvent(
                stream=proof.stream,
                event='status',
                comments='Received comments: {comments}'.format(comments=comments),
                noted_by=proof.stream.supervisor
            )
            prodevent.save()
        return proof
