__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import calendar
import datetime
import re

from django import forms
from django.forms.widgets import Widget, Select
from django.utils.dates import MONTHS
from django.utils.safestring import mark_safe



__all__ = ('MonthYearWidget',)

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')


class MonthYearWidget(Widget):
    """
    A Widget that splits date input into two <select> boxes for month and year,
    with 'day' defaulting to the first of the month.

    Based on SelectDateWidget, in

    django/trunk/django/forms/extras/widgets.py


    """
    none_value = (0, '---')
    month_field = '%s_month'
    year_field = '%s_year'

    def __init__(self, attrs=None, end=False, required=False):
        self.attrs = attrs or {}
        self.required = required
        self.today = datetime.date.today()
        self.round_to_end = end

        # Years
        this_year = self.today.year
        self.year_choices = [(i, i) for i in range(this_year - 4, this_year + 1)]
        if not self.required:
            self.year_choices.insert(0, self.none_value)

        # Month
        self.month_choices = dict(MONTHS.items())
        if not self.required:
            self.month_choices[self.none_value[0]] = self.none_value[1]
        self.month_choices = sorted(self.month_choices.items())

    def sqeeze_form_group(self, html, width=6):
        return '<div class="form-group col-md-{width}">{html}</div>'.format(width=width, html=html)

    def render(self, name, value, attrs=None, renderer=None):
        try:
            year_val, month_val = value.year, value.month
        except AttributeError:
            year_val = month_val = None
            if isinstance(value, (str, bytes)):
                match = RE_DATE.match(value)
                if match:
                    year_val, month_val, day_val = [int(v) for v in match.groups()]

        output = []

        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        if hasattr(self, 'month_choices'):
            local_attrs = self.build_attrs({'id': self.month_field % id_})
            s = Select(choices=self.month_choices, attrs={'class': 'form-control'})
            select_html = s.render(self.month_field % name, month_val, local_attrs)
            output.append(self.sqeeze_form_group(select_html))

        if hasattr(self, 'year_choices'):
            local_attrs = self.build_attrs({'id': self.year_field % id_})
            s = Select(choices=self.year_choices, attrs={'class': 'form-control'})
            select_html = s.render(self.year_field % name, year_val, local_attrs)
            output.append(self.sqeeze_form_group(select_html))

        return mark_safe(u'\n'.join(output))

    @classmethod
    def id_for_label(self, id_):
        return '%s_month' % id_

    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)

        if y == m == "0":
            return None

        # Defaults for `month`
        if m == "0":
            m = "12" if self.round_to_end else "1"

        if y == "0":
            if self.round_to_end:
                y = self.year_choices[-1][0]
            else:
                index = 0
                if not self.required:
                    index += 1
                y = self.year_choices[index][0]
        if y and m:
            # Days are used for filtering, but not communicated to the user
            if self.round_to_end:
                d = calendar.monthrange(int(y), int(m))[1]
            else:
                d = '1'
            return '%s-%s-%s' % (y, m, d)
        return data.get(name, None)


class ModelChoiceFieldwithid(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return '%s (id = %i)' % (super().label_from_instance(obj), obj.id)
