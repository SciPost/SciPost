from django.contrib.sites.models import Site
from django.db.models import Field, ForeignObjectRel
from django.db.models.fields.related import RelatedField


def get_current_domain():
    try:
        return Site.objects.get_current().domain
    except:
        return "fake.domain"


def merge(old, new):
    """
    Merge two model instances, `old` and `new`, by:
    - copying all the fields from `old` to `new` if they are not already set
    - updating all (reverse) relations from `old` to `new`
    """
    model = old.__class__

    for field in model._meta.get_fields():
        accessor = field.name or field.get_accessor_name()
        old_value = getattr(old, accessor, None)

        if isinstance(field, Field):
            # If new object has a value for the field, skip it
            # otherwise, set the value from the old object
            if getattr(new, accessor, None) is None:
                setattr(new, accessor, old_value)
        elif isinstance(field, RelatedField) or isinstance(field, ForeignObjectRel):
            # Handle object relations
            related_object = field
            manager = related_object.related_model.objects

            # Guard against missing related object field names
            if not hasattr(related_object, "field"):
                continue

            field_name = related_object.field.name

            if related_object.one_to_one:
                # For one-to-one relations, we get the related objects from the manager
                # and anull (let go) the attribute of the new object
                # so that it can be attached it to the old object
                # =====================
                # Equivalent to:
                # new.field_name = None
                # old.field_name = new
                manager.filter(**{field_name: new}).update(**{field_name: None})
                manager.filter(**{field_name: old}).update(**{field_name: new})
            elif related_object.many_to_many:
                # For many-to-many relations, `old_value` is a manager
                # and we can add the related objects to the new object
                if accessor is not None and old_value is not None:
                    getattr(new, accessor).add(*old_value.all())
                else:
                    for related_queryset in manager.filter(**{field_name: old}):
                        getattr(related_queryset, accessor).remove(old)
                        getattr(related_queryset, accessor).add(new)
            elif related_object.one_to_many:
                # For one-to-many relations, we get the related objects from the manager
                # and update the foreign key to the new object
                manager.filter(**{field_name: old}).update(**{field_name: new})
            else:
                # Handle many-to-one relations by setting the attribute
                # of the new object if it is not already set
                if getattr(new, accessor) is None:
                    setattr(new, accessor, old_value)

        else:
            # Handle fields by setting the attribute of the new object
            # if it is not already set
            if getattr(new, accessor) is None:
                setattr(new, accessor, old_value)

    # Save both objects
    new.save()
    old.save()
