__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from collections.abc import Collection
from django import forms
from crispy_forms.layout import Div, Field, Layout
from crispy_bootstrap5.bootstrap5 import FloatingField
from common.forms import CrispyFormMixin, SearchForm
from common.utils.python import recursive_get_attr
from tasks.tasks.task import Task
from tasks.tasks.task_kinds import get_all_task_kinds


class TaskListSearchForm(CrispyFormMixin, SearchForm[Task]):
    q = forms.CharField(label="Search", required=False)

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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.task_kinds = get_all_task_kinds(self.user)
        super().__init__(*args, **kwargs)

    def get_form_layout(self) -> Layout:
        div_block_ordering = Div(
            Div(Field("orderby"), css_class="col-6"),
            Div(Field("ordering"), css_class="col-6"),
            css_class="row mb-0",
        )

        return Layout(
            Div(FloatingField("q"), css_class="col-12"),
            div_block_ordering,
        )

    # Override method from SearchForm with incompatible signature
    # This is one of the rare cases where instead of a queryset,
    # we return a concrete collection of Task objects.
    def search(self) -> Collection[Task]:
        search_text = self.cleaned_data.get("q", "")
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
