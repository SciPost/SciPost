__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from copy import deepcopy
from dataclasses import dataclass, field
from types import NoneType
from typing import Any, TypeVar
from django.forms import Field


T = TypeVar("T")
Options = dict[str, T]


class BaseOptions:
    """
    Base class for options
    """

    prefix: str = ""

    @classmethod
    def get_available_options(cls):
        return [key for key in cls.__dict__.keys() if not key.startswith("__")]

    @classmethod
    def get_option_fields(cls) -> Options[Field]:
        """
        Returns a dictionary of string keys and Field values,
        mapping the options to their respective fields.
        The keys are prefixed with the class prefix.
        """
        options: Options[Field] = {}
        for option_key in dir(cls):
            if option_key.startswith("__"):
                continue

            option_value = getattr(cls, option_key)
            if isinstance(option_value, Field):
                # Deepcopy the field to avoid modifying the original (in global scope)
                option_field = deepcopy(option_value)
                # Try to remove the prefix from the label if it is present
                if option_field.label is None:
                    option_field.label = cls.unprefixed(option_key).title()
                options[cls.prefix + option_key] = option_field

        return options

    @classmethod
    def unprefixed(cls, key: str) -> str:
        if key.startswith(cls.prefix):
            return key[len(cls.prefix) :]
        return key

    @classmethod
    def parse_prefixed_options(cls, options: Options[Any]) -> Options[Any]:
        """
        Returns a dictionary with only unprefixed and valid options.
        """
        return {
            cls.unprefixed(k): cls.coerce_value_types(v)
            for k, v in options.items()
            if cls.unprefixed(k) in cls.get_available_options()
        }

    @classmethod
    def coerce_value_types(cls, value: T) -> T | None:
        """
        Coerces the value to the correct type, e.g. "None" to None.
        """
        if value == "None":
            return None
        return value


@dataclass
class GraphModelField:
    name: str = ""
    label: str = ""
    type: "type" = NoneType
    permissions: list[str] = field(default_factory=list[str])
