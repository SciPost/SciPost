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

def days_duration_human(duration: int) -> str:
    """
    Returns the most appropriate human-readable representation of a duration in days.
    """
    years = duration // 365
    months = (duration % 365) // 30
    days = duration % 30

    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months > 1 else ''}")
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")

    return ", ".join(parts) if parts else "0 days"