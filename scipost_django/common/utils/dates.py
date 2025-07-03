__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from datetime import date, datetime
from typing import Any, TypeGuard

DateRepresentation = str | date | datetime


def date_to_str(date_rep: DateRepresentation) -> str:
    date_str = date_rep
    if isinstance(date_str, datetime):
        date_str = date_str.date()
    if isinstance(date_str, date):
        return date_str.strftime("%Y-%m-%d")

    return date_str


def is_date_representation(value: Any) -> TypeGuard[DateRepresentation]:
    if isinstance(value, str):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    else:
        return isinstance(value, (date, datetime))
