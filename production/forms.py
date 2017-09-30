import datetime

from django import forms
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

    def get_events(self, officer=None):
        qs = ProductionEvent.objects.filter(duration__isnull=False,
                                            noted_on__month=self.cleaned_data['month'],
                                            noted_on__year=self.cleaned_data['year'])
        if officer:
            qs.filter(noted_by=officer)
        return qs.order_by('noted_by')
