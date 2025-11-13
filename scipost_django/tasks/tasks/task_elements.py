__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from dataclasses import dataclass

from common.utils.models import model_eval_attr

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .task import Task


@dataclass
class TaskBadge:
    name: str
    field_name: str
    value: str
    color_name: str = "secondary"

    def as_html(self) -> str:
        badge_template = '<span class="badge rounded-pill text-white bg-{color_name} bg-opacity-75">{field_name}: {value}</span>'
        return badge_template.format(
            color_name=self.color_name,
            field_name=self.field_name,
            value=self.value,
        )

    @classmethod
    def default_builder(
        cls,
        property_key: str,
        name: str | None = None,
        field_name: str | None = None,
        color_name: str = "secondary",
    ):
        def badge(task: "Task") -> TaskBadge:
            last_property = property_key.split(".")[-1].replace("_", " ")
            name_final = name or f"{task.kind.__name__}_{last_property}"
            field_name_final = field_name or last_property.title()
            return cls(
                name=name_final,
                field_name=field_name_final,
                value=model_eval_attr(obj=task.data["object"], attr_path=property_key),
                color_name=color_name,
            )

        return badge
