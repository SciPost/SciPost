__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from django.urls import reverse_lazy

from .task import Task


@dataclass
class TaskAction:
    tag: Literal["a", "button"]
    css_class: str = "btn"
    content: str = ""
    kwargs: dict = field(default_factory=dict)

    @staticmethod
    def attrs_str(attrs: dict) -> str:
        return " ".join(f'{k}="{v}"' for k, v in attrs.items())

    @property
    def attrs(self) -> dict:
        return self.kwargs.get("attrs", {})

    @property
    def as_html(self) -> str:
        element = '<{tag} {attrs} class="{css_class}">{content}</{tag}>'
        return element.format(
            tag=self.tag,
            attrs=self.attrs_str(self.attrs),
            css_class=self.css_class,
            content=self.content,
        )


class ViewAction(TaskAction):
    def __init__(self, url: str, content: str = "View"):
        self.url = url

        return super().__init__(
            tag="a",
            content=content,
            kwargs={"attrs": {"href": self.url}},
        )

    @staticmethod
    def default_builder(
        reverse_url_str: str, content: str = "View"
    ) -> Callable[[Task], TaskAction]:
        def action(task: Task) -> TaskAction:
            return ViewAction(
                reverse_lazy(reverse_url_str, kwargs={"pk": task.data["object"].pk}),
                content,
            )

        return action
