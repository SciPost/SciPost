__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.contrib.auth import get_user_model
from django.utils.dates import MONTHS
from django.db.models import Sum
from django.utils import timezone

from ajax_select.fields import AutoCompleteSelectField

from .models import Subsidy, WorkLog

today = timezone.now().date()


class SubsidyForm(forms.ModelForm):
    organization = AutoCompleteSelectField('organization_lookup')

    class Meta:
        model = Subsidy
        fields = ['organization', 'subsidy_type', 'description',
                  'amount', 'amount_publicly_shown', 'status',
                  'date', 'date_until']


class WorkLogForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.types = kwargs.pop('log_types', False)
        super().__init__(*args, **kwargs)
        if self.types:
            self.fields['log_type'] = forms.ChoiceField(choices=self.types)

    class Meta:
        model = WorkLog
        fields = (
            'comments',
            'log_type',
            'duration',
        )
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
            'duration': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'})
        }


class LogsMonthlyActiveFilter(forms.Form):
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

        users = get_user_model().objects.filter(
            work_logs__work_date__month=self.cleaned_data['month'],
            work_logs__work_date__year=self.cleaned_data['year']).distinct()
        output = []
        for user in users:
            logs = user.work_logs.filter(
                work_date__month=self.cleaned_data['month'],
                work_date__year=self.cleaned_data['year'])
            output.append({
                'logs': logs,
                'duration': logs.aggregate(total=Sum('duration')),
                'user': user
            })

        return output
