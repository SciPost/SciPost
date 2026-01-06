__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


def recursive_get_attr(obj: object, attr: str) -> object:
    """
    Recursively get attributes from an object.
    e.g. recursive_get_attr(obj, "a.b.c") is equivalent to obj.a.b.c
    """
    if "." in attr:
        first, rest = attr.split(".", 1)
        return recursive_get_attr(getattr(obj, first), rest)
    return getattr(obj, attr)
