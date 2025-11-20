__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from abc import abstractmethod
from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.db.models import Q, QuerySet
from django.template import Template, loader
from django.utils import timezone

from .task_elements import TaskBadge

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from .task_action import TaskAction


@dataclass
class Task:
    user: "User | None"
    kind: "type[TaskKind]"
    data: dict = field(default_factory=dict)

    @property
    def actions(self) -> Collection["TaskAction"]:
        return [action(self) for action in self.kind.actions]

    @property
    def badges(self) -> Collection["TaskBadge"]:
        badges = [badge(self) for badge in getattr(self.kind, "badges", [])]
        if self.due_date:
            badges.insert(
                0,
                TaskBadge(
                    name="due_date",
                    field_name="Due",
                    value=self.due_date.strftime("%Y-%m-%d"),
                    color_name="warning",
                    color_func=lambda _: "danger"
                    if self.due_date <= timezone.now()
                    else "warning"
                    if self.due_date <= timezone.now() + timezone.timedelta(days=15)
                    else "success",
                )
                if self.due_date
                else None,
            )
        return badges

    @property
    def as_html(self) -> str:
        return self.kind.template().render({"task": self})

    @property
    def title(self) -> str:
        return self.kind.task_title.format(**self.data)

    @property
    def due_date(self) -> timezone.datetime:
        return self.data.get("due_date", self.kind.get_default_due_date())


class TaskKind:
    name: str
    task_title: str
    description: str = ""
    actions: Collection[Callable[[Task], "TaskAction"]]
    user: "User | None" = None
    template_name: str = "tasks/task.html"

    @staticmethod
    @abstractmethod
    def get_queryset() -> "QuerySet":
        """Return a queryset of task data from which Task instances are created."""
        pass

    @staticmethod
    @abstractmethod
    def search_query(text: str) -> Q:
        """Create a filter query for a given text."""
        return Q()

    @classmethod
    def search(cls, text: str) -> "QuerySet":
        """Return a queryset of tasks that match the search text."""
        search_query = cls.search_query(text)
        return cls.get_queryset().filter(search_query)

    @classmethod
    def get_tasks(cls, text: str | None = None) -> Collection[Task]:
        return [
            Task(user=cls.user, kind=cls, data=data) for data in cls.get_task_data(text)
        ]

    @classmethod
    def get_task_data(cls, text: str | None = None) -> Collection[dict]:
        """Return a collection of dictionaries to be used as task data."""
        qs = cls.search(text) if text else cls.get_queryset()
        return [cls.get_task_map(obj) for obj in qs]

    @staticmethod
    def get_task_map(obj) -> dict:
        """Maps the queryset to a collection of dictionaries to be used as task data."""
        return {"object": obj}

    @classmethod
    def template(cls) -> Template:
        return loader.get_template(cls.template_name)

    @staticmethod
    @abstractmethod
    def is_user_eligible(user: "User") -> bool:
        return user.is_staff

    @staticmethod
    def get_default_due_date() -> timezone.datetime:
        return timezone.now()
