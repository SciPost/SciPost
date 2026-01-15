__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import abc
import datetime
import json

from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html

from common.utils import get_current_domain

from . import constants

from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from submissions.models.submission import Submission


class BaseAction:
    """A pending action for the Submission's refereeing cycle."""

    txt = ""
    url = "#"
    url2 = "#"
    submission = None

    def __init__(self, object=None, **kwargs):
        self._objects = [object] if object else []
        if "submission" in kwargs:
            self.submission = kwargs.pop("submission")
        self.id = (
            "%s.%i" % (object.__class__.__name__, object.id)
            if object
            else self.__class__.__name__
        )

    def __eq__(self, other):
        return (
            getattr(self, "submission", 0) == getattr(other, "submission", 0)
            and self.id == other.id
        )

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.id)

    def _format_text(self, text, obj=None):
        if obj is None and self._objects:
            obj = self._objects[0]

        timedelta = datetime.timedelta()
        deadline = datetime.timedelta()

        if hasattr(obj, "date_invited") and obj.date_invited:
            timedelta = timezone.now() - obj.date_invited
        if hasattr(obj, "submission") and obj.submission.reporting_deadline:
            deadline = obj.submission.reporting_deadline - timezone.now()
        else:
            deadline = None

        # Add the domain name to the url so that it is clickable in the email
        if self.url.startswith("/"):
            base_url = "https://" + get_current_domain() + self.url
        else:
            base_url = self.url

        return text.format(
            count=len(self._objects),
            object=obj.__class__.__name__,
            author=obj.author.profile.formal_name if getattr(obj, "author", None) else "",
            referee=obj.referee.full_name if getattr(obj, "referee", None) else "",
            days=timedelta.days,
            deadline=deadline.days if deadline else "-",
            deadline_min=-deadline.days if deadline else "-",
            url=base_url,
            url2=self.url2,
        )

    def as_text(self):
        return " ".join([e for e in self])

    def __iter__(self):
        if self._objects:
            for obj in self._objects:
                yield format_html(self._format_text(self.txt, obj=obj))
        else:
            yield format_html(self._format_text(self.txt))

    def __str__(self):
        return self.as_text()


class VettingAction(BaseAction):
    txt = '{author} has delivered a {object}. <a href="{url}">Please vet it</a>.'

    @property
    def url(self):
        match self.id.split("."):
            case "Comment", comment_id:
                return reverse("comments:vet_submitted_comment", args=[comment_id])
            case "Report", report_id:
                return reverse("submissions:vet_submitted_report", args=[report_id])
            case _:
                return "{}#current-contributions".format(
                    reverse(
                        "submissions:editorial_page",
                        args=(self.submission.preprint.identifier_w_vn_nr,),
                    )
                )


class NoRefereeResponseAction(BaseAction):
    txt = (
        "Referee {referee} has not responded for {days} days."
        " Consider sending a reminder or cancelling the invitation."
    )


class DeadlineAction(BaseAction):
    txt = (
        "Referee {referee} has accepted to send a Report "
        "(with {deadline} days left), but not yet delivered it. Consider sending a reminder."
    )


class OverdueAction(BaseAction):
    txt = (
        "Referee {referee} has accepted to send a Report "
        "({deadline_min} days overdue), but not yet delivered it. Consider sending a reminder."
    )


class CycleChoiceAction(BaseAction):
    txt = "Choose the submission cycle to proceed with."


class NoEICRecommendationAction(BaseAction):
    needs_referees = False

    @property
    def txt(self):
        if self.needs_referees:
            txt = (
                "The refereeing deadline has passed and you have received no Reports yet."
                ' Please <a href="{url}">extend the reporting deadline</a> '
                "and consider sending a reminder to your referees."
            )
        else:
            txt = (
                "The refereeing deadline has passed. Please either "
                '<a href="{url}">extend it</a>, '
                'or <a href="{url2}">formulate your Editorial Recommendation</a>.'
            )
        return txt

    @property
    def url(self):
        return "{}#reporting-deadline".format(
            reverse(
                "submissions:editorial_page",
                args=(self.submission.preprint.identifier_w_vn_nr,),
            )
        )

    @property
    def url2(self):
        return reverse(
            "submissions:eic_recommendation",
            args=(self.submission.preprint.identifier_w_vn_nr,),
        )


class NeedRefereesAction(BaseAction):
    def __init__(self, object=None, **kwargs):
        self.minimum_number_of_referees = kwargs.pop("minimum_number_of_referees")
        self.number_of_invitations = kwargs.pop("number_of_invitations")
        super().__init__(object, **kwargs)

    @property
    def txt(self):
        if self.number_of_invitations == 0:
            text = "No Referees have been invited."
        elif self.number_of_invitations == 1:
            text = "Only 1 Referee has been invited."
        else:
            text = f"Only {self.number_of_invitations} Referees have been invited."
        text += ' At least {minimum} should be. <a href="{url}">Invite a referee here</a>.'.format(
            minimum=self.minimum_number_of_referees,
            url=reverse(
                "submissions:select_referee",
                args=(self.submission.preprint.identifier_w_vn_nr,),
            ),
        )
        return text


class BaseCycle(abc.ABC):
    """A base blueprint for the Submission refereeing cycle.

    The refereeing process may be defined differently for every cycle class by its own
    specific properties. The cycle class will then take care of the required actions,
    permissions and the overall refereeing process.
    """

    can_invite_referees = True

    def __init__(self, submission: "Submission"):
        self._submission = submission
        self._required_actions: list["BaseAction"] = []
        self._actions_exhausted = False

    @property
    def required_actions(self) -> Generator["BaseAction", None, None]:
        if self._required_actions and self._actions_exhausted:
            yield from self._required_actions

        else:
            for action in self.yield_required_actions():
                self._required_actions.append(action)
                yield action
            self._actions_exhausted = True

    @property
    def days_for_refereeing(self):
        return 0

    @property
    def minimum_number_of_referees(self):
        if (
            self._submission.proceedings
            and self._submission.proceedings.minimum_referees
        ):
            return self._submission.proceedings.minimum_referees
        return 3  # Three by default

    @cached_property
    def has_required_actions(self):
        return bool(next(iter(self.required_actions), None))

    def yield_required_actions(self) -> Generator["BaseAction", None, None]:
        """Gather the required actions list and populate self._required_actions."""
        # Comments requiring vetting (including replies and recursive comments)
        yield from (
            VettingAction(comment, submission=self._submission)
            for comment in self._submission.comments_set_complete().awaiting_vetting()
        )

        # Reports requiring vetting
        yield from (
            VettingAction(report, submission=self._submission)
            for report in self._submission.reports.awaiting_vetting()
        )

        # If this cycle is not the latest one in the thread, return early, skipping other actions
        if not self._submission.is_latest:
            return

        if not self._submission.refereeing_cycle:
            # Submission is a resubmission: EIC has to determine which cycle to proceed with.
            yield CycleChoiceAction(submission=self._submission)
            return  # If no cycle is chosen. Make this a first priority!

        # The EIC is late with formulating a Recommendation.
        if self._submission.eic_recommendation_required:
            if self._submission.reporting_deadline_has_passed:
                action = NoEICRecommendationAction(submission=self._submission)
                action.needs_referees = (
                    not self._submission.reports.non_draft().exists()
                )
                yield action

        if self.can_invite_referees and self._submission.in_stage_in_refereeing:
            # Referees required in this cycle.
            non_cancelled_or_refused_invitations = (
                self._submission.referee_invitations.exclude(
                    Q(cancelled=True) | Q(accepted=False)
                )
            )
            nr_active_invitations = non_cancelled_or_refused_invitations.count()
            nr_unique_reports = self._submission.nr_unique_thread_vetted_reports
            nr_unfulfilled_accepted_invitations = (
                self._submission.referee_invitations.filter(accepted=True)
                .exclude(Q(cancelled=True) | Q(fulfilled=True))
                .count()
            )
            has_enough_invitations = (
                nr_active_invitations >= self.minimum_number_of_referees
            )
            reports_and_accepted_suffice = (
                self._submission.submitted_to.minimal_nr_of_reports > 0
                and (nr_unique_reports + nr_unfulfilled_accepted_invitations)
                # minimal_nr_of_reports is really the number of referees needed
                >= self._submission.submitted_to.minimal_nr_of_reports
            )
            # Only show the action if reports don't suffice
            # and there are not enough active invitations (pending or accepted)
            if not (reports_and_accepted_suffice or has_enough_invitations):
                yield NeedRefereesAction(
                    number_of_invitations=nr_active_invitations,
                    minimum_number_of_referees=self.minimum_number_of_referees,
                    submission=self._submission,
                )

        referee_invitations = self._submission.referee_invitations.needs_attention()
        for referee_invitation in referee_invitations:
            if referee_invitation.needs_response:
                # Invited, but no response
                yield NoRefereeResponseAction(
                    referee_invitation,
                    submission=self._submission,
                )
            elif referee_invitation.is_overdue:
                yield OverdueAction(
                    referee_invitation,
                    submission=self._submission,
                )

            elif referee_invitation.needs_fulfillment_reminder:
                yield DeadlineAction(
                    referee_invitation,
                    submission=self._submission,
                )

    def as_text(self):
        """Return a *short* description of the current status of the submission cycle."""
        texts = []

        recommendation = self._submission.recommendation
        if recommendation:
            texts.append("Thank you for formulating your Editorial Recommendation.")
            if recommendation.status == constants.VOTING_IN_PREP:
                texts.append(
                    "The Editorial Administration is now preparing it for voting."
                )
            elif recommendation.status == constants.PUT_TO_VOTING:
                texts.append("It is now put to voting in the college.")

        if self._submission.status == self._submission.RESUBMITTED:
            new_sub_id = (
                self._submission.get_latest_version().preprint.identifier_w_vn_nr
            )
            txt = (
                "The Submission has been resubmitted as {identifier},"
                ' <a href="{url}">go to its editorial page</a>.'
            )
            texts.append(
                txt.format(
                    url=reverse("submissions:editorial_page", args=(new_sub_id,)),
                    identifier=new_sub_id,
                )
            )
        elif self._submission.in_stage_in_production:
            texts.append(
                "The SciPost production team is working on the proofs for publication."
            )
        elif self._submission.status == self._submission.REJECTED:
            texts.append("The Submission is rejected for publication.")
        elif self._submission.status == self._submission.WITHDRAWN:
            texts.append("The authors have withdrawn the Submission.")
        elif self._submission.status == self._submission.PUBLISHED:
            texts.append("The Submission has been published as ")
            for publication in self._submission.publications.published():
                texts.append(
                    '<a href="{url}">{doi}</a> '.format(
                        url=publication.get_absolute_url(),
                        doi=publication.doi_label,
                    )
                )
        elif self._submission.status == self._submission.REFEREEING_CLOSED:
            if recommendation:
                texts.append("The refereeing round is closed.")
            else:
                texts.append(
                    (
                        "The refereeing round is closed "
                        "and you have not formulated an Editorial Recommendation."
                    )
                )

        if not self.has_required_actions and not texts:
            texts.append("No action required.")
        elif self.has_required_actions:
            texts.append("<strong>Please see your required actions below.</strong>")
        return format_html(" ".join(texts))

    def __str__(self):
        return self.as_text()

    def reset_refereeing_round(self):
        """
        Set the Submission status to IN_REFEREEING and reset the reporting deadline to None.
        """

        self._submission.status = self._submission.IN_REFEREEING
        self._submission.reporting_deadline = None
        self._submission.save()

    def get_default_refereeing_deadline(self):
        """
        Get the default refereeing deadline for the Submission.
        """

        deadline = timezone.now() + datetime.timedelta(days=self.days_for_refereeing)
        return deadline

    def reinvite_referees(self, referees):
        """
        Duplicate and reset RefereeInvitations and send `reinvite` mail.

        referees - (list of) RefereeInvitation instances
        """
        from mails.utils import DirectMailUtil

        for referee in referees:
            invitation = referee
            invitation.pk = None  # Duplicate, do not remove the old invitation
            invitation.submission = self._submission
            invitation.reset_content()
            invitation.date_invited = timezone.now()
            invitation.save()
            mail_sender = DirectMailUtil(
                "referees/reinvite_contributor_to_referee", invitation=invitation
            )
            mail_sender.send_mail()


class RegularCycle(BaseCycle):
    """
    Regular refereeing cycle, used for the first round of refereeing.
    Duration differs based on the journal, according to article 3.6.3 of the by-laws.
    """

    @property
    def days_for_refereeing(self):
        return self._submission.submitted_to.refereeing_period.days


class ShortCycle(BaseCycle):
    """
    Short (two weeks) version of the regular refereeing cycle, used for resubmissions on request
    by the editor.
    """

    @property
    def days_for_refereeing(self):
        return 2 * 7  # 2 weeks

    @property
    def minimum_number_of_referees(self):
        return 1


class DirectCycle(BaseCycle):
    """
    Refereeing cycle without refereeing. The editor directly formulates an EICRecommendation.
    """

    can_invite_referees = False

    def yield_required_actions(self):
        """Gather the required actions list and populate self._required_actions."""
        actions = []
        for action in super().yield_required_actions():
            actions.append(action)
            yield action

        # Always show `EICRec required` action disregarding the refereeing deadline.
        no_recom_action = NoEICRecommendationAction(submission=self._submission)
        if (
            self._submission.eic_recommendation_required
            and no_recom_action not in actions
        ):
            yield no_recom_action
