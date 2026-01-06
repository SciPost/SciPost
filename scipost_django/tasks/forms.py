__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from collections.abc import Collection
from itertools import chain
from typing import Dict
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field
from crispy_bootstrap5.bootstrap5 import FloatingField
from common.utils.python import recursive_get_attr
from tasks.tasks.task import Task
from tasks.tasks.task_kinds import get_all_task_kinds


class TaskListSearchForm(forms.Form):
    search = forms.CharField(label="Search", required=False)

    orderby = forms.ChoiceField(
        label="Order by",
        choices=[
            ("", "-----"),
            ("kind.name", "Kind"),
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
            Div(FloatingField("search"), css_class="col-12"),
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
        def recursive_get_attr(obj, attr):
            """
            Recursively get attributes from an object.
            e.g. recursive_get_attr(obj, "a.b.c") is equivalent to obj.a.b.c
            """
            if "." in attr:
                first, rest = attr.split(".", 1)
                return recursive_get_attr(getattr(obj, first), rest)
            return getattr(obj, attr)

        search_text = self.cleaned_data.get("search", "")
        orderby = self.cleaned_data.get("orderby", "")
        ordering = self.cleaned_data.get("ordering", "-")

        tasks = [
            task
            for task_kind in self.task_kinds
            for task in task_kind.get_tasks(search_text)
        ]

        reverse_ordering = ordering == "-"
        if orderby:
            tasks = sorted(
                tasks,
                key=lambda x: recursive_get_attr(x, orderby),
                reverse=reverse_ordering,
            )

        return tasks
