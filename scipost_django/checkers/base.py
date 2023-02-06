__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import operator

from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet


class ObjectChecker:
    model = None
    queryset = None
    filter_kwargs = {}
    max_nr_breakages = 10

    def __init__(self):
        self.breakages = []

    def get_queryset(self):
        if self.queryset:
            queryset = self.queryset
            if (isinstance(queryset, QuerySet)):
                queryset = queryset.all()
        elif self.model:
            queryset = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} needs a model or a queryset."
            )
        return queryset.filter(**self.filter_kwargs)

    def check(self):
        self.breakages = []
        for object in self.get_queryset():
            self._check_object(object)
            if len(self.breakages) >= self.max_nr_breakages:
                return

    def repair_object(self, object):
        raise NotImplementedError

    def repair_breakages(self):
        while len(self.breakages) > 0:
            breakage = self.breakages.pop(0)
            self.repair_object(breakage["object"])


class SingleObjectCheckerMixin:
    def get_object_info_dict(self, object):
        return {
            "checker": self.__class__.__name__,
            "checker_type": self.checker_type,
            "object": object,
            "object_class": object.__class__,
            "pk": object.id,
            "url": object.get_absolute_url(),
        }


class ObjectCheckerAttrEqualsValue(SingleObjectCheckerMixin, ObjectChecker):
    checker_type = "attribute == expected value"
    attribute = None
    expected_value = None

    def __init__(self):
        if not self.attribute:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} needs an `attribute` to check."
            )
        elif not self.expected_value:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} needs an `expected_value` to check against."
            )
        super().__init__()

    def _check_object(self, object):
        """
        Check that object has an attribute with expected value.
        """
        value = operator.attrgetter(self.attribute)(object)
        if value != self.expected_value:
            info = self.get_object_info_dict(object)
            info["attribute"] = self.attribute
            info["expected_value"] = self.expected_value
            info["value"] = value
            self.breakages.append(info)


class ObjectCheckerAttrEqualsAttr(SingleObjectCheckerMixin, ObjectChecker):
    checker_type = "attribute1 == attribute2"
    attribute1 = None
    attribute2 = None

    def __init__(self):
        if not self.attribute1 or not self.attribute2:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} needs `attribute1`, `attribute2` to check."
            )
        super().__init__()

    def _check_object(self, object):
        """
        Check that object has a pair of attributes with correlated value.
        """
        value1 = operator.attrgetter(self.attribute1)(object)
        value2 = operator.attrgetter(self.attribute2)(object)
        if value2 != value1:
            info = self.get_object_info_dict(object)
            info["attribute1"] = self.attribute1
            info["value1"] = value1
            info["attribute2"] = self.attribute2
            info["value2"] = value2
            self.breakages.append(info)
