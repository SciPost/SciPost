__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib.postgres.lookups import Unaccent
from django.db import models
from django.db.models import Q, Exists, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from colleges.models.fellowship import Fellowship
from comments.models import Comment
from common.utils.db import SplitString
from common.utils.text import initialize
from submissions.models.qualification import Qualification
from submissions.models.readiness import Readiness

from .. import constants

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...scipost.models import Contributor
    from profiles.models import Profile


class SubmissionQuerySet(models.QuerySet):
    ##################################
    # Shortcuts for status filtering #
    ##################################
    def incoming(self):
        return self.filter(status=self.model.INCOMING)

    def admissible(self):
        return self.filter(status=self.model.ADMISSIBLE)

    def admission_failed(self):
        return self.filter(status=self.model.ADMISSION_FAILED)

    def preassignment(self):
        return self.filter(status=self.model.PREASSIGNMENT)

    def preassignment_failed(self):
        return self.filter(status=self.model.PREASSIGNMENT_FAILED)

    def seeking_assignment(self):
        return self.filter(status=self.model.SEEKING_ASSIGNMENT)

    def assignment_failed(self):
        return self.filter(status=self.model.ASSIGNMENT_FAILED)

    def refereeing_in_preparation(self):
        return self.filter(status=self.model.REFEREEING_IN_PREPARATION)

    def in_refereeing(self):
        return self.filter(status=self.model.IN_REFEREEING)

    def refereeing_closed(self):
        return self.filter(status=self.model.REFEREEING_CLOSED)

    def awaiting_resubmission(self):
        return self.filter(status=self.model.AWAITING_RESUBMISSION)

    def resubmitted(self):
        return self.filter(status=self.model.RESUBMITTED)

    def voting_in_preparation(self):
        return self.filter(status=self.model.VOTING_IN_PREPARATION)

    def in_voting(self):
        return self.filter(status=self.model.IN_VOTING)

    def awaiting_decision(self):
        return self.filter(status=self.model.AWAITING_DECISION)

    def accepted_in_target(self):
        return self.filter(status=self.model.ACCEPTED_IN_TARGET)

    def accepted_in_alternative_awaiting_puboffer_acceptance(self):
        return self.filter(
            status=self.model.ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE
        )

    def accepted_in_alternative(self):
        return self.filter(status=self.model.ACCEPTED_IN_ALTERNATIVE)

    def rejected(self):
        return self.latest().filter(status=self.model.REJECTED)

    def withdrawn(self):
        return self.latest().filter(status=self.model.WITHDRAWN)

    def published(self):
        return self.filter(status=self.model.PUBLISHED)

    ### Managers for stages ####

    def in_stage_incoming(self):
        return self.filter(status__in=self.model.STAGE_INCOMING)

    def stage_incoming_completed(self):
        return self.filter(status__in=self.model.STAGE_INCOMING_COMPLETED_STATUSES)

    def in_stage_preassignment(self):
        return self.filter(status__in=self.model.STAGE_PREASSIGNMENT)

    def stage_preassignment_completed(self):
        return self.filter(status__in=self.model.STAGE_PREASSIGNMENT_COMPLETED_STATUSES)

    def in_stage_assignment(self):
        return self.filter(status__in=self.model.STAGE_ASSIGNMENT)

    def stage_assignment_completed(self):
        return self.filter(status__in=self.model.STAGE_ASSIGNMENT_COMPLETED_STATUSES)

    def in_stage_refereeing_in_preparation(self):
        return self.filter(status__in=self.model.STAGE_REFEREEING_IN_PREPARATION)

    def stage_refereeing_in_preparation_completed(self):
        return self.filter(
            status__in=self.model.STAGE_REFEREEING_IN_PREPARATION_COMPLETED_STATUSES
        )

    def in_stage_in_refereeing(self):
        return self.filter(status__in=self.model.STAGE_IN_REFEREEING)

    def stage_in_refereeing_completed(self):
        return self.filter(status__in=self.model.STAGE_IN_REFEREEING_COMPLETED_STATUSES)

    def in_stage_decisionmaking(self):
        return self.filter(status__in=self.model.STAGE_DECISIONMAKING)

    def stage_decisionmaking_completed(self):
        return self.filter(status__in=self.model.STAGE_DECIDED)

    def in_state_in_production(self):
        return self.filter(status__in=self.model.STAGE_IN_PRODUCTION)

    #### Other managers mixing statuses ####

    def under_consideration(self):
        return self.filter(status__in=self.model.UNDER_CONSIDERATION)

    def treated(self):
        """Returns Submissions (stream heads) whose streams are fully processed."""
        return self.filter(status__in=self.model.TREATED)

    def accepted(self):
        return self.filter(
            status__in=[
                self.model.ACCEPTED_IN_TARGET,
                self.model.ACCEPTED_IN_ALTERNATIVE,
            ]
        )

    ######################################
    # End shortcuts for status filtering #
    ######################################

    def latest(self):
        return self.exclude(status=self.model.RESUBMITTED)

    @staticmethod
    def Q_profile_possibly_in_author_list(profile: "Profile"):
        """
        Return Submissions for which the profile is possibly in the author list.
        """
        first_name_initial = initialize(profile.first_name)
        return Q(author_list__unaccent__icontains=profile.last_name) & (
            Q(author_list__unaccent__icontains=profile.first_name)
            | Q(author_list__unaccent__contains=first_name_initial)
        )

    def with_potential_unclaimed_author(self, contributor: "Contributor"):
        """
        Return Submissions for which the contributor could potentially be an author.
        """
        qs = (
            self.exclude(authors=contributor)
            .exclude(authors_claims=contributor)
            .exclude(authors_false_claims=contributor)
        )

        if profile := contributor.profile:
            qs = qs.filter(self.Q_profile_possibly_in_author_list(profile))

        return qs

    def in_pool(self, user, latest: bool = True, historical: bool = False):
        """
        Filter for Submissions (current or historical) in user's pool,
        excluding CoIs and possible authorship.

        If `historical==False`: only submissions UNDER_CONSIDERATION,
        otherwise show full history.

        For non-EdAdmin: user must have active Fellowship and
        be listed in Submission's Fellowship.

        For Senior Fellows, exclude INCOMING status;
        for other Fellows, also exclude PREASSIGNMENT.
        """
        from submissions.models.submission import Submission

        contributor: Contributor | None = getattr(user, "contributor", None)
        if contributor is None:
            return self.none()

        if not (contributor.is_ed_admin or contributor.is_active_fellow):
            return self.none()

        qs = (
            self.all()
            .annot_authors_have_nonexpired_coi_with_profile(contributor.profile)
            .annotate(
                fellowship_in_submission_fellowships=Exists(
                    Submission.fellows.through.objects.filter(
                        submission_id=models.OuterRef("pk"),
                        fellowship_id__in=contributor.fellowships.active(),
                    )
                )
            )
        )

        # remove Submissions for which a conflict of interest exists:
        qs = qs.exclude(authors_have_nonexpired_coi_with_profile=True)

        # Exclude Submissions where the contributor is a real author, claims authorship,
        # or their name could be in the author list but also has not claimed the association is false.
        qs = qs.exclude(
            Q(authors_claims=contributor)
            | Q(authors=contributor)
            | (
                self.Q_profile_possibly_in_author_list(contributor.profile)
                & ~Q(authors_false_claims=contributor)
            )
        )

        if latest:
            qs = qs.latest()
        if not historical:
            qs = qs.filter(status__in=self.model.UNDER_CONSIDERATION)

        # for non-EdAdmin, filter: in Submission's Fellowship
        if not user.contributor.is_ed_admin:
            qs = qs.filter(fellowship_in_submission_fellowships=True)

        if user.contributor.is_scipost_admin:
            pass
        # Fellows can't see incoming and (non-Senior) preassignment
        elif user.contributor.is_active_senior_fellow:
            qs = qs.exclude(status__in=[self.model.INCOMING])
        elif user.contributor.is_active_fellow:
            qs = qs.exclude(status__in=[self.model.INCOMING, self.model.PREASSIGNMENT])

        return qs

    def in_pool_filter_for_eic(
        self,
        user,
        latest: bool = True,
        historical: bool = False,
    ):
        """Return the set of Submissions the user is Editor-in-charge for.

        If user is an Editorial Administrator: keep any EiC.
        """
        qs = self.in_pool(user, latest=latest, historical=historical)
        if user.is_authenticated and not user.contributor.is_ed_admin:
            qs = qs.filter(editor_in_charge__dbuser=user)
        return qs

    def filter_for_author(self, user):
        """Return the set of Submissions for which the user is a registered author."""
        if not hasattr(user, "contributor"):
            return self.none()
        return self.filter(authors=user.contributor)

    def assigned(self):
        """Return submissions with assigned Editor-in-charge."""
        return self.filter(editor_in_charge__isnull=False)

    def without_eic(self):
        """Return Submissions that still need Editorial Assignment."""
        return self.filter(
            status__in=[self.model.PREASSIGNMENT, self.model.SEEKING_ASSIGNMENT]
        )

    def public(self):
        """Return all publicly available Submissions."""
        return self.filter(visible_public=True)

    def public_listed(self):
        """List all public Submissions if not published and submitted.

        Implement: Use this filter to also determine, using a optional user argument,
                   if the query should be filtered or not as a logged in EdCol Admin
                   should be able to view *all* submissions.
        """
        return self.filter(visible_public=True).exclude(
            status__in=[self.model.RESUBMITTED, self.model.PUBLISHED]
        )

    def public_latest(self):
        """
        This query contains set of public() submissions, filtered to only the latest available
        version.
        """
        return self.latest().public()

    def originally_submitted(self, from_date, until_date):
        """
        Returns the submissions originally received between from_date and until_date
        (including subsequent resubmissions, even if those came in later).
        """
        thread_hashes = []
        for sub in self.filter(
            is_resubmission_of__isnull=True,
            submission_date__range=(from_date, until_date),
        ):
            thread_hashes.append(sub.thread_hash)
        return self.filter(thread_hash__in=thread_hashes)

    def unpublished(self):
        """Return unpublished Submissions."""
        return self.exclude(status=self.model.PUBLISHED)

    def open_for_reporting(self):
        """Return Submissions open for reporting."""
        return self.filter(open_for_reporting=True)

    def reports_needed(self):
        """
        Return Submissions for which the nr of Reports is less than required by target Journal.
        """
        qs = self.prefetch_related("reports", "submitted_to").annotate(
            nr_reports=models.Count("reports")
        )
        ids_list = [
            s.id
            for s in qs.all()
            if (s.nr_reports < s.submitted_to.minimal_nr_of_reports)
        ]
        return self.filter(id__in=ids_list)

    def open_for_commenting(self):
        """Return Submission that allow for commenting."""
        return self.filter(open_for_commenting=True)

    def needs_coauthorships_update(self):
        """Return set of Submissions that need a Coauthorships update."""
        return self.filter(needs_coauthorships_update=True)

    def has_editor_invitations_to_be_sent(self):
        from submissions.models import EditorialAssignment

        """Return Submissions that have EditorialAssignments that still need to be sent."""
        return self.filter(
            editorial_assignments__status=EditorialAssignment.STATUS_PREASSIGNED,
        )

    def candidate_for_resubmission(self, user):
        """
        Return all Submissions that are open for resubmission specialised for a certain User.
        """
        if not hasattr(user, "contributor"):
            return self.none()

        return self.filter(
            status__in=[
                self.model.AWAITING_RESUBMISSION,
            ],
            authors=user.contributor,
        )

    def undergoing_voting(self, longer_than_days=None):
        from submissions.models import EICRecommendation
        from submissions.models.submission import SubmissionEvent

        qs = self.filter(
            id__in=EICRecommendation.objects.put_to_voting().values("submission")
        )

        if longer_than_days:
            older_than_date = timezone.now() - datetime.timedelta(days=longer_than_days)
            qs = qs.annotate(
                voting_event_date=models.Subquery(
                    SubmissionEvent.objects.filter(
                        submission=models.OuterRef("pk"),
                        text__iregex=r"Voting on recommendation.+?started",
                    )
                    .order_by("-created")
                    .values("created")[:1]
                )
            ).filter(voting_event_date__lt=older_than_date)

        return qs

    def annot_authors_have_nonexpired_coi_with_profile(self, profile: "Profile"):
        """
        Annotate Submissions with a boolean indicating if there is a non-expired conflict of interest
        with any of the authors.
        """
        from ethics.models import ConflictOfInterest
        from submissions.models.submission import SubmissionAuthorProfile

        return self.annotate(
            authors_have_nonexpired_coi_with_profile=Exists(
                ConflictOfInterest.objects.all()
                .annotate(
                    submission_id=models.OuterRef("id"),  # to use in subquery below
                    involves_author=models.Exists(
                        SubmissionAuthorProfile.objects.filter(
                            Q(profile_id=models.OuterRef("profile_id"))
                            | Q(profile_id=models.OuterRef("related_profile_id")),
                            submission_id=models.OuterRef("submission_id"),
                        )
                    ),
                    submission_exempted=Q(
                        exempted_submission_threads__contains=[
                            models.OuterRef("thread_hash")
                        ]
                    ),
                )
                .filter(involves_author=True)
                .involving_profile(profile)
                .valid_on_date()
                .exclude(submission_exempted=True)
            ),
        )

    def annot_qualified_expertise_by(self, fellow):
        """
        Annotate Submissions with the expertise level of the Qualification provided by a Fellow.
        """
        return self.annotate(
            qualification_expertise=models.Subquery(
                fellow.qualification_set.filter(submission=models.OuterRef("pk"))
                .order_by("-datetime")
                .values("expertise_level")[:1]
            )
        )

    def annot_readiness_status_by(self, fellow):
        """
        Annotate Submissions with the readiness status of the Readiness provided by a Fellow.
        """
        return self.annotate(
            readiness_status=models.Subquery(
                fellow.readiness_set.filter(submission=models.OuterRef("pk"))
                .order_by("-datetime")
                .values("status")[:1]
            )
        )

    def annot_clearance_by(self, profile):
        """
        Annotate Submissions with a boolean indicating if the profile has provided a Clearance.
        """
        return self.annotate(
            has_clearance=models.Exists(
                profile.submission_clearances.filter(submission=models.OuterRef("pk"))
            )
        )

    def annot_fully_appraised_by(self, fellow: Fellowship):
        """
        Annotate Submissions with a boolean indicating if the fellow has fully appraised the submission.
        Full appraisal means one of the following states:
        - Qualification, Readiness and Clearance are all provided
        - Qualification is not sufficient for taking charge
        - Readiness is "Perhaps Later"
        """
        return (
            self.annot_qualified_expertise_by(fellow)
            .annot_readiness_status_by(fellow)
            .annot_clearance_by(fellow.contributor.profile)
            .annotate(
                is_fully_appraised=Coalesce(
                    Q(
                        qualification_expertise__isnull=False,
                        readiness_status__isnull=False,
                        has_clearance=True,
                    )
                    | Q(
                        qualification_expertise__in=Qualification.EXPERTISE_NOT_QUALIFIED
                    )
                    | Q(readiness_status=Readiness.STATUS_PERHAPS_LATER),
                    Value(False),
                    output_field=models.BooleanField(),
                )
            )
        )

    def annot_thread_sequence_order(self):
        """
        Annotate Submissions with their sequence order in the thread.
        """
        from submissions.models.submission import Submission

        return self.annotate(
            thread_sequence_order=models.Subquery(
                Submission.objects.filter(
                    thread_hash=models.OuterRef("thread_hash"),
                    submission_date__lte=models.OuterRef("submission_date"),
                )
                .values("thread_hash")
                .annotate(nr_submissions=models.Count("thread_hash"))
                .values("nr_submissions")[:1]
            ),
        )

    def annot_is_latest(self):
        """
        Annotate Submissions with a boolean indicating if they are the latest in their thread.
        """
        from submissions.models.submission import Submission

        return self.annotate(
            is_latest=~Exists(
                Submission.objects.filter(
                    thread_hash=models.OuterRef("thread_hash"),
                    submission_date__gt=models.OuterRef("submission_date"),
                )
            )
        )

    def annot_recommendation_id(self):
        """
        Annotate Submissions with the id of the latest recommendation (if any).
        """
        from submissions.models import EICRecommendation

        return self.annotate(
            recommendation_id=models.Subquery(
                EICRecommendation.objects.filter(submission=models.OuterRef("pk"))
                .active()
                .order_by("-version")
                .values("id")[:1]
            )
        )

    def annot_editorial_decision_id(self):
        """
        Annotate Submissions with the id of the latest editorial decision (if any).
        """
        from submissions.models import EditorialDecision

        return self.annotate(
            editorial_decision_id=models.Subquery(
                EditorialDecision.objects.filter(submission=models.OuterRef("pk"))
                .nondeprecated()
                .order_by("-version")
                .values("id")[:1]
            )
        )

    def exclude_not_qualified_for_fellow(self, fellow: Fellowship):
        """
        Exclude Submissions that the Fellow has indicated they are not qualified to judge.
        """
        return self.annotate(
            is_not_qualified=Exists(
                Qualification.objects.filter(
                    submission=models.OuterRef("pk"),
                    fellow=fellow,
                ).not_qualified()
            )
        ).exclude(is_not_qualified=True)

    def comments_set_complete(self):
        """Return Comments on Submissions, Reports and other Comments."""
        qs = Comment.objects.filter(
            Q(submissions__in=self)
            | Q(reports__submission__in=self)
            | Q(comments__reports__submission__in=self)
            | Q(comments__submissions__in=self)
        )
        # Add recursive comments:
        for c in qs:
            if c.nested_comments:
                qs = qs | c.all_nested_comments().all()
        return qs.distinct()

    def reports(self):
        """Return all Reports for Submissions."""
        from submissions.models import Report

        return Report.objects.filter(submission__in=self)

    def author_full_name_in_list(self, author_full_name):
        """Return Submissions where the full author name is in the list."""
        return self.annotate(
            author_name=Value(author_full_name),
            authors_split=SplitString(Unaccent("author_list"), delimiter=", "),
        ).filter(authors_split__contains=Unaccent("author_name"))


class SubmissionEventQuerySet(models.QuerySet):
    def for_edadmin(self):
        """Return all events that are visible to EdAdmin."""
        return self.filter(
            event__in=[
                constants.EVENT_FOR_EDADMIN,
                constants.EVENT_FOR_EIC,
                constants.EVENT_GENERAL,
            ]
        )

    def for_eic(self):
        """Return all events that are visible to Editor-in-charge of a submission."""
        return self.filter(event__in=[constants.EVENT_FOR_EIC, constants.EVENT_GENERAL])

    def for_author(self):
        """Return all events that are visible to author(s) of a submission."""
        return self.filter(
            event__in=[constants.EVENT_FOR_AUTHOR, constants.EVENT_GENERAL]
        )

    def last_hours(self, hours=24):
        """Return all events of the last `hours` hours."""
        return self.filter(
            created__gte=timezone.now() - datetime.timedelta(hours=hours)
        )

    def iThenticate_plagiarism_report_to_be_uploaded(self):
        """Return Submissions that has not been sent to iThenticate for their plagiarism check."""
        return self.filter(
            models.Q(iThenticate_plagiarism_report__isnull=True)
            | models.Q(iThenticate_plagiarism_report__status=constants.STATUS_WAITING)
        ).distinct()

    def iThenticate_plagiarism_report_to_be_updated(self):
        """Return Submissions for which their iThenticateReport has not received a report yet."""
        return self.filter(iThenticate_plagiarism_report__status=constants.STATUS_SENT)
