__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from dataclasses import dataclass

from common.utils.models import model_eval_attr

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .task import Task


@dataclass
class TaskBadge:
    name: str
    field_name: str
    value: str
    unit: str = ""
    color_name: str = "secondary"
    color_func: Callable[[Any], str] | None = None

    BADGE_TEMPLATE = '<span class="badge rounded-pill text-white {color_class}">{field_name}: {value} {unit}</span>'

    def as_html(self) -> str:
        color_class = self.get_color_class(self.value)
        return self.BADGE_TEMPLATE.format(color_class=color_class, **self.__dict__)

    def get_color_class(self, value: Any = None) -> str:
        if self.color_func is None or value is None:
            return f"bg-{self.color_name} bg-opacity-75"

        color_eval = self.color_func(value)
        return f"bg-{color_eval} bg-opacity-75"

    @classmethod
    def default_builder(
        cls,
        property_key: str,
        **kwargs: Any,
    ):
        def badge(task: "Task") -> TaskBadge:
            value = model_eval_attr(obj=task.data["object"], attr_path=property_key)

            last_property = property_key.split(".")[-1].replace("_", " ")

            kwargs.setdefault("name", f"{task.kind.__name__}_{last_property}")
            kwargs.setdefault("field_name", last_property.title())

            return cls(value=value, **kwargs)

        return badge
