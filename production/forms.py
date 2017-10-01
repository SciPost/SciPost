import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.utils.dates import MONTHS
from django.db.models import Sum

from .models import ProductionUser, ProductionStream, ProductionEvent

today = datetime.datetime.today()


class ProductionEventForm(forms.ModelForm):
    class Meta:
        model = ProductionEvent
        fields = (
            'event',
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


class AssignSupervisorForm(forms.ModelForm):
    class Meta:
        model = ProductionStream
        fields = ('supervisor',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supervisor'].queryset = self.fields['supervisor'].queryset.filter(
            user__groups__name='Production Supervisor')


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
