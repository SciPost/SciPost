__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# import calendar
import datetime
import re

from django.forms.widgets import Widget, Select, NumberInput
from django.utils.dates import MONTHS
from django.utils.safestring import mark_safe

__all__ = ('DateWidget',)

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')


class DateWidget(Widget):
    """
    A Widget that splits date input into two <select> boxes for month and year,
    with 'day' defaulting to the first of the month.

    Based on SelectDateWidget, in

    django/trunk/django/forms/extras/widgets.py


    """
    none_value = (0, 'Month')
    day_field = '%s_day'
    month_field = '%s_month'
    year_field = '%s_year'

    def __init__(self, attrs=None, end=False, required=False):
        self.attrs = attrs or {}
        self.required = required
        self.today = datetime.date.today()
        self.round_to_end = end

        # Month
        self.month_choices = dict(MONTHS.items())
        if not self.required:
            self.month_choices[self.none_value[0]] = self.none_value[1]
        self.month_choices = sorted(self.month_choices.items())

    def sqeeze_form_group(self, html, width=4):
        return '<div class="col-md-{width}">{html}</div>'.format(width=width, html=html)

    def render(self, name, value, attrs=None, renderer=None):
        try:
            year_val, month_val, day_val = value.year, value.month, value.day
        except AttributeError:
            year_val = month_val = day_val = None
            if isinstance(value, (str, bytes)):
                match = RE_DATE.match(value)
                if match:
                    year_val, month_val, day_val = [int(v) for v in match.groups()]

        output = []

        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        # Day input
        local_attrs = self.build_attrs({'id': self.day_field % id_})
        s = NumberInput(attrs={'class': 'form-control', 'placeholder': 'Day'})
        select_html = s.render(self.day_field % name, day_val, local_attrs)
        output.append(self.sqeeze_form_group(select_html))

        # Month input
        if hasattr(self, 'month_choices'):
            local_attrs = self.build_attrs({'id': self.month_field % id_})
            s = Select(choices=self.month_choices, attrs={'class': 'form-control'})
            select_html = s.render(self.month_field % name, month_val, local_attrs)
            output.append(self.sqeeze_form_group(select_html))

        # Year input
        local_attrs = self.build_attrs({'id': self.year_field % id_})
        s = NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'})
        select_html = s.render(self.year_field % name, year_val, local_attrs)
        output.append(self.sqeeze_form_group(select_html))

        output = '<div class="row mb-0">{0}</div>'.format(u'\n'.join(output))

        return mark_safe(output)

    @classmethod
    def id_for_label(self, id_):
        return '%s_month' % id_

    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = data.get(self.day_field % name)

        if m == "0":
            return None
        return '%s-%s-%s' % (y, m, d)
