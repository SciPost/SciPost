__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.contrib.auth import get_user_model
from django.utils.dates import MONTHS
from django.db.models import Sum
from django.utils import timezone

from ajax_select.fields import AutoCompleteSelectField

from scipost.fields import UserModelChoiceField

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


class LogsActiveFilter(forms.Form):
    """
    Filter work logs given the requested date range and users.
    """

    employee = UserModelChoiceField(
        queryset=get_user_model().objects.filter(work_logs__isnull=False), required=False)
    month = forms.ChoiceField(
        choices=[(None, 9 * '-')] + [(k, v) for k, v in MONTHS.items()], required=False)
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

    def filter(self):
        """Filter work logs and return in output-convenient format."""
        output = []
        if self.is_valid():
            user_qs = get_user_model().objects.filter(
                work_logs__isnull=False, work_logs__work_date__year=self.cleaned_data['year'])
            if self.cleaned_data['employee']:
                # Get as a queryset instead of single instead.
                user_qs = user_qs.filter(id=self.cleaned_data['employee'].id)
            user_qs = user_qs.distinct()

            output = []
            for user in user_qs:
                logs = user.work_logs.filter(work_date__year=self.cleaned_data['year'])
                if self.cleaned_data['month']:
                    logs = logs.filter(work_date__month=self.cleaned_data['month'])
                logs = logs.distinct()

                if logs:
                    # If logs exists for given filters
                    output.append({
                        'logs': logs,
                        'duration': logs.aggregate(total=Sum('duration')),
                        'user': user,
                    })
        return output
