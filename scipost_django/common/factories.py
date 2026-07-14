import random
from typing import Callable

from django.db.models import Model
import factory

from typing import TypeVar

M = TypeVar("M", bound=Model)
N = TypeVar("N", bound=Model)


def set_or_create_consistent_related_field(
    factory: factory.Factory[M],
    object_count: tuple[int, int] | int = 1,
    consistent_fields: dict[str, str] = {},
):
    """
    A decorator for factory post_generation hooks that sets a related field to a random number of existing objects,
    creating new ones if necessary. Objects are filtered/created according to conformance criteria via `consistent_fields`.

    :param factory: The factory to use for creating new objects if necessary. Factor's `Meta.model` is used to determine the model for querying existing objects.
    :param object_count: A range (min, max) to sample from, or a fixed number of objects to set on the related field.
    :param consistent_fields: A mapping of related field name to the field name on the factory.
    e.g. `{"contributor__profile": "profile"}` means `.filter(contributor__profile=self.profile)` when looking for existing objects.
    """
    model: M = factory._meta.model

    def decorator(func: Callable) -> None:

        def wrapper(self: N, create: bool, extracted: list[M], **kwargs):
            if not create:
                return

            try:
                accessor = getattr(self, func.__name__)
            except Exception as e:
                raise ValueError(
                    f"Could not determine accessor for field '{func.__name__}': {e}"
                )

            if extracted:
                accessor.set(extracted)
                func(self, create, extracted, **kwargs)
                return

            consistency_kwargs = {
                related_name: getattr(self, field_name) if field_name else self
                for related_name, field_name in consistent_fields.items()
            }
            existing_objects = list(
                model.objects.filter(**consistency_kwargs).order_by("?")
            )

            if isinstance(object_count, int):
                objects_to_add_nr = object_count
            elif len(object_count) == 2:
                objects_to_add_nr = max(0, random.randint(*object_count))
            else:
                raise ValueError("object_count must be an int or a tuple of two ints")

            objects_to_create_nr = max(0, objects_to_add_nr - len(existing_objects))
            objects_created = factory.create_batch(
                objects_to_create_nr, **consistency_kwargs
            )
            objects_to_add = existing_objects[:objects_to_add_nr] + objects_created

            accessor.set(objects_to_add)

            func(self, create, extracted, **kwargs)

        return wrapper

    return decorator
