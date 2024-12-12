__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from collections.abc import Collection
from itertools import chain
from typing import Dict
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field
from tasks.tasks.task import Task
from tasks.tasks.task_kinds import get_all_task_kinds


class TaskListSearchForm(forms.Form):
    search = forms.CharField(label="Search", required=False)

    orderby = forms.ChoiceField(
        label="Order by",
        choices=[
            ("", "-----"),
            ("kind__name", "Type"),
            ("title", "Title"),
            ("due_date", "Due date"),
        ],
        initial="",
        required=False,
    )
    ordering = forms.ChoiceField(
        label="Ordering",
        choices=[
            ("-", "Descending"),
            ("+", "Ascending"),
        ],
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.task_kinds = get_all_task_kinds(self.user)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()

        div_block_ordering = Div(
            Div(Field("orderby"), css_class="col-6"),
            Div(Field("ordering"), css_class="col-6"),
            css_class="row mb-0",
        )

        self.helper.layout = Div(
            Div(Field("search"), css_class="col-12"),
            div_block_ordering,
        )

    def apply_filter_set(self, filters: Dict, none_on_empty: bool = False):
        # Apply the filter set to the form
        for key in self.fields:
            if key in filters:
                self.fields[key].initial = filters[key]
            elif none_on_empty:
                if isinstance(self.fields[key], forms.MultipleChoiceField):
                    self.fields[key].initial = []
                else:
                    self.fields[key].initial = None

    def search_results(self) -> Collection[Task]:
        search_text = self.cleaned_data.get("search", "")
        orderby = self.cleaned_data.get("orderby", "")
        ordering = self.cleaned_data.get("ordering", "-")

        tasks = [
            task
            for task_kind in self.task_kinds
            for task in task_kind.get_tasks(search_text)
        ]

        return tasks
