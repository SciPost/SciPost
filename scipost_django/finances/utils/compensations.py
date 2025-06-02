from enum import Enum

from django.db.models import Q, Model

from common.utils.models import parametrize_query


class CompensationStrategy(Enum):
    SELF = ("self", "Self", Q(organization="organization.id"))
    CHILDREN = ("children", "Children", Q(organization="organization.children"))
    PARENT = ("parent", "Parent", Q(organization="organization.parent"))
    SIBLINGS = ("siblings", "Siblings", Q(organization="organization.parent.children"))
    IDS = ("ids", "IDs", Q(organization__in="compensation_strategies_details.ids"))
    COUNTRIES = ("countries", "Countries", Q(organization__country__in="compensation_strategies_details.countries"))
    FUNDERS = ("funders", "Funders", Q(publication__generic_funders__in="compensation_strategies_details.funders"))
    SPECIALTIES = ("specialties", "Specialties", Q(publication__specialties__slug__in="compensation_strategies_details.specialties"))
    ANY = ("any", "Any", Q(organization__isnull=False))
    NONE = ("none", "None", Q(organization__isnull=True))

    @classmethod
    def get_default_strategies_keys_list(cls) -> "CompensationStrategy":
        return [cls.SELF.key, cls.PARENT.key, cls.CHILDREN.key]

    @property
    def key(self) -> str:
        return self.value[0]

    @property
    def display_str(self) -> str:
        return self.value[1]

    @property
    def base_Q(self) -> Q:
        return self.value[2]

    @property
    def priority(self) -> int:
        return [key for key, _ in self.get_choices()].index(self.key)

    def get_filter(self, obj: Model) -> Q:
        return parametrize_query(self.base_Q, obj)

    @classmethod
    def get_choices(cls):
        return [(strategy.key, strategy.display_str) for strategy in cls]

    @classmethod
    def from_key(cls, key: str) -> "CompensationStrategy":
        """
        Get a CompensationStrategy instance from its key.
        """
        for strategy in cls:
            if strategy.key == key:
                return strategy
        raise ValueError(f"Unknown CompensationStrategy key: {key}")

    @classmethod
    def __getitem__(cls, item: str) -> "CompensationStrategy":
        return cls.from_key(item)
