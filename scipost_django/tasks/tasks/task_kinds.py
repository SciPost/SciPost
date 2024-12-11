__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from collections.abc import Collection
from django.db.models import (
    F,
    Q,
    DateTimeField,
    Exists,
    OuterRef,
    QuerySet,
    Subquery,
    Sum,
)
from django.db.models.functions import Cast, Coalesce
from django.urls import reverse_lazy
from django.utils import timezone
from scipost.templatetags.user_groups import is_financial_admin
from tasks.tasks.task import TaskKind
from tasks.tasks.task_action import ViewAction

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import User


def get_all_task_kinds(user: "User | None" = None) -> Collection[type[TaskKind]]:
    """Return all TaskKind classes, optionally filtered by user eligibility."""
    classes: list[type[TaskKind]] = []
    for cls in globals().values():
        if isinstance(cls, type) and issubclass(cls, TaskKind) and cls != TaskKind:
            cls.user = user
            classes.append(cls)

    # Filter the classes based on user eligibility
    if user is not None:
        classes = [cls for cls in classes if cls.is_user_eligible(user)]

    return classes


class ScheduleSubsidyPayments(TaskKind):
    name = "Schedule Subsidy Payments"
    task_title = "Schedule Payments for {object}"
    description = "Schedule payments for subsidies that are not part of a collective."
    actions = [
        ViewAction.default_builder("finances:subsidy_details"),
        ViewAction.default_builder("finances:subsidy_update", "Edit"),
    ]

    @staticmethod
    def is_user_eligible(user):
        return is_financial_admin(user)

    @staticmethod
    def get_queryset() -> "QuerySet":
        from finances.models import Subsidy, SubsidyPayment

        return (
            Subsidy.objects.all()
            .annotate(
                payment_sum=Sum("payments__amount"),
                amount_high_bound=1.05 * F("amount"),
                amount_low_bound=0.95 * F("amount"),
                schedule_complete=(
                    Q(payment_sum__gte=F("amount_low_bound"))
                    & Q(payment_sum__lte=F("amount_high_bound"))
                ),
                has_payments=Exists(
                    SubsidyPayment.objects.filter(subsidy=OuterRef("id"))
                ),
                schedule_blank=Q(has_payments=False) & ~Q(amount=0),
            )
            .filter(
                Q(collective__isnull=True)
                & (Q(schedule_blank=True) | Q(schedule_complete=False))
            )
        )


class ScheduleSubsidyCollectivePayments(TaskKind):
    name = "Schedule Subsidy Collective Payments"
    task_title = "Schedule Collective Payments for {object}"
    description = "Schedule payments for subsidies that are part of a collective."
    actions = [
        lambda t: ViewAction(
            url=reverse_lazy(
                "finances:subsidy_collective_details",
                kwargs={"collective_id": t.data["object"].pk},
            )
        ),
        lambda t: ViewAction(
            url=reverse_lazy(
                "finances:subsidy_collective_update",
                kwargs={"collective_id": t.data["object"].pk},
            ),
            content="Edit",
        ),
    ]

    @staticmethod
    def is_user_eligible(user):
        return is_financial_admin(user)

    @staticmethod
    def get_queryset() -> "QuerySet":
        from finances.models.subsidy import SubsidyCollective

        return (
            SubsidyCollective.objects.all()
            .annotate(
                collective_payment_sum=Sum("subsidies__payments__amount"),
                collective_amount_sum=Sum("subsidies__amount"),
                sum_high_bound=1.05 * F("collective_amount_sum"),
                sum_low_bound=0.95 * F("collective_amount_sum"),
                schedule_complete=(
                    Q(collective_payment_sum__gte=F("sum_low_bound"))
                    & Q(collective_payment_sum__lte=F("sum_high_bound"))
                ),
            )
            .filter(Q(schedule_complete=False))
        )


class SendSubsidyInvoiceTask(TaskKind):
    name = "Send Invoice"
    task_title = "Send Invoice for {object}"
    description = (
        "Send an invoice for a subsidy that has payments without proof of payment."
    )
    actions = [
        ViewAction.default_builder("finances:subsidy_details"),
        ViewAction.default_builder("finances:subsidy_update", "Edit"),
    ]

    @staticmethod
    def is_user_eligible(user):
        return is_financial_admin(user)

    @classmethod
    def get_task_data(cls) -> Collection[dict]:
        return [{"object": obj, "due_date": obj.due_date} for obj in cls.get_queryset()]

    @staticmethod
    def get_queryset() -> "QuerySet":
        from finances.models import Subsidy, SubsidyPayment
        from finances.constants import SUBSIDY_PROMISED, SUBSIDY_UPTODATE

        return (
            Subsidy.objects.all()
            .annotate(
                due_date=Subquery(
                    SubsidyPayment.objects.filter(
                        subsidy=OuterRef("id"), proof_of_payment__isnull=True
                    )
                    .order_by("date_scheduled")
                    .values("date_scheduled")[:1]
                )
            )
            .filter(
                Q(due_date__isnull=False)
                & (Q(status=SUBSIDY_PROMISED) | Q(status=SUBSIDY_UPTODATE))
            )
        )


class CheckSubsidyPaymentTask(TaskKind):
    name = "Check Payment"
    task_title = "Check Payment for {object}"
    description = "Check the payment status for a subsidy that has been invoiced."
    actions = [
        ViewAction.default_builder("finances:subsidy_details"),
        ViewAction.default_builder("finances:subsidy_update", "Edit"),
    ]

    @staticmethod
    def is_user_eligible(user):
        return is_financial_admin(user)

    @classmethod
    def get_task_data(cls) -> Collection[dict]:
        return [{"object": obj, "due_date": obj.due_date} for obj in cls.get_queryset()]

    @staticmethod
    def get_queryset() -> "QuerySet":
        from finances.models import Subsidy, SubsidyPayment
        from finances.constants import SUBSIDY_INVOICED

        now = timezone.now()

        return (
            Subsidy.objects.all()
            .annotate(
                due_date=Coalesce(
                    Subquery(
                        SubsidyPayment.objects.filter(
                            subsidy=OuterRef("id"), proof_of_payment__isnull=True
                        )
                        .order_by("date_scheduled")
                        .values("date_scheduled")[:1]
                    )
                    + timezone.timedelta(days=31),
                    Cast(now, DateTimeField()),
                ),
            )
            .filter(Q(status=SUBSIDY_INVOICED))
        )
