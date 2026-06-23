__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.template.defaulttags import comment
from django.urls import reverse, reverse_lazy
from common.utils.attachments import RelatedAttachment, attach_related
from mails.views import MailView
from pins.models import Note
from production.constants import PROOFS_SENT, PROOFS_SOURCE_REQUESTED
from scipost.mixins import PermissionsMixin

from scipost.models import Remark
from scipost.forms import RemarkForm
from colleges.models import PotentialFellowship, Fellowship
from colleges.permissions import (
    fellowship_required,
    fellowship_or_admin_required,
)
from ethics.models import Coauthorship
from mails.utils import DirectMailUtil
from scipost.permissions import HTMXResponse, permission_required_htmx
from submissions.models import (
    EditorialAssignment,
    EICRecommendation,
    Submission,
)
from submissions.forms import (
    SubmissionPoolSearchForm,
    EditorialAssignmentForm,
)
from submissions.models.decision import EditorialDecision


@login_required
@fellowship_or_admin_required()
def pool(request, identifier_w_vn_nr=None):
    """
    Listing of Submissions for purposes of editorial handling.
    """
    nr_potfels_to_vote_on = PotentialFellowship.objects.to_vote_on(
        request.user.contributor
    ).count()
    nr_potential_author_conflicts = Submission.objects.with_potential_unclaimed_author(
        request.user.contributor
    ).count()
    recs_to_vote_on = EICRecommendation.objects.user_must_vote_on(request.user)
    recs_current_voted = EICRecommendation.objects.user_current_voted(request.user)
    assignments_to_consider = EditorialAssignment.objects.invited().filter(
        to=request.user.contributor
    )
    initial = {"status": Submission.SEEKING_ASSIGNMENT}
    if identifier_w_vn_nr:
        initial = {"identifier": identifier_w_vn_nr}
    context = {
        "nr_potential_author_conflicts": nr_potential_author_conflicts,
        "nr_potfels_to_vote_on": nr_potfels_to_vote_on,
        "recs_to_vote_on": recs_to_vote_on,
        "recs_current_voted": recs_current_voted,
        "assignments_to_consider": assignments_to_consider,
        "form": SubmissionPoolSearchForm(initial=initial, request=request),
    }
    return render(request, "submissions/pool/pool.html", context)


@login_required
@fellowship_or_admin_required()
def pool_hx_submission_list(request):
    form = SubmissionPoolSearchForm(request.POST or None, request=request)

    submissions = (
        form.search()
        .select_related(
            "preprint",
            "editor_in_charge",
            "editor_in_charge__profile",
            "submitted_to",
            "is_resubmission_of",
            "submitted_by__profile",
        )
        .prefetch_related(
            "red_flags",
            "specialties",
            "submitted_by__profile__red_flags",
            "remarks",
        )
        .annot_recommendation_id()
        .annot_editorial_decision_id()
    )

    attach_related(
        submissions,
        RelatedAttachment(
            "recommendation_id",
            "recommendation",
            EICRecommendation.objects.all()
            .select_related("for_journal")
            .prefetch_related(
                "eligible_to_vote",
                "voted_for",
                "voted_against",
                "voted_abstain",
            ),
        ),
        RelatedAttachment(
            "editorial_decision_id",
            "editorial_decision",
            EditorialDecision.objects.all(),
        ),
    )

    paginator = Paginator(submissions, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index
    context = {
        "count": count,
        "page_obj": page_obj,
        "start_index": start_index,
    }
    return render(request, "submissions/pool/_hx_submission_list.html", context)


@login_required
@fellowship_or_admin_required()
def pool_hx_submission_details_contents(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user, historical=True),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    context = {"remark_form": RemarkForm(), "submission": submission}
    return render(
        request, "submissions/pool/_hx_submission_details_contents.html", context
    )


@login_required
@fellowship_or_admin_required()
def _hx_submission_tab(request, identifier_w_vn_nr, tab):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user, historical=True, latest=False),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    context = {
        "submission": submission,
        "tab": tab,
    }
    if tab == "remarks":
        context["remark_form"] = RemarkForm()

    return render(request, "submissions/pool/_hx_submission_tab.html", context)


@login_required
@fellowship_or_admin_required()
def _hx_submission_fellows_tab(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user, historical=True, latest=False),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    context = {
        "submission": submission,
        "submission_fellow_undecided_coauthorships_count": (
            Coauthorship.objects.all()
            .between_profiles(
                submission.author_profiles.values("profile"),
                submission.fellows.values("contributor__profile"),
            )
            .unverified()
            .count()
        ),
    }
    return render(request, "submissions/pool/_submission_fellows.html", context)


@permission_required_htmx("scipost.can_mark_submission_on_hold")
def _hx_submission_toggle_on_hold(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    # Guard against statuses which may not be put on hold
    VALID_STATUSES = [
        Submission.INCOMING,
        Submission.ADMISSIBLE,
        Submission.PREASSIGNMENT,
        Submission.VOTING_IN_PREPARATION,
    ]
    if submission.status not in VALID_STATUSES:
        return HTMXResponse(
            "This Submission is not in a state where it can be put on hold.",
            tag="danger",
        )

    submission.on_hold = not submission.on_hold
    submission.save()

    # Create an internal note on this submission with the reason provided through HX-Prompt
    if submission.on_hold:
        note = Note(
            visibility=Note.VISIBILITY_INTERNAL,
            author=request.user.contributor,
            regarding_content_type=ContentType.objects.get_for_model(Submission),
            regarding_object_id=submission.id,
            title="Submission put on hold",
            description=request.headers.get("HX-Prompt"),
        )
        note.save()

    message = "Submission has been {verb} hold.".format(
        verb="put on" if submission.on_hold else "taken off"
    )

    submission.add_event_for_edadmin(message)
    messages.success(request, message)

    return render(
        request,
        "submissions/pool/_hx_submission_details.html",
        {"submission": submission},
    )

@permission_required_htmx("scipost.can_mark_submission_dormant")
def _hx_submission_toggle_dormant(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )

    def infer_pre_dormant_status(submission: Submission):
        """
        Infer the status of a Submission before it was marked as dormant.
        This is used to restore the status when unmarking a Submission as dormant.
        """

        if submission.status != Submission.DORMANT:
            raise ValueError("Submission is not marked as dormant.")

        # Any accepted submission must have a decision, therefore it's awaiting resubmission otherwise.
        if not ((decision := submission.editorial_decision) and decision.publish):
            return Submission.AWAITING_RESUBMISSION
        elif decision.for_journal == submission.submitted_to:
            return Submission.ACCEPTED_IN_TARGET
        elif decision.is_fixed_and_accepted:
            return Submission.ACCEPTED_IN_ALTERNATIVE
        else:
            return Submission.ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE

    def can_be_marked_dormant(submission: Submission):
        """
        A Submission may be marked as dormant if it is:
        - Awaiting resubmission
        - Awaiting puboffer acceptance
        - Is accepted, and its production stream is:
            - awaiting source files
            - awaiting acceptance of proofs
        """
        from production.models import ProductionStream
        from production.constants import PROOFS_SOURCE_REQUESTED, PROOFS_SENT

        if submission.status in [
            Submission.AWAITING_RESUBMISSION,
            Submission.ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE,
        ]:
            return True
        elif submission.in_stage_in_production:
            try:
                prod_stream_status = submission.production_stream.status
            except ProductionStream.DoesNotExist:
                return False

            if prod_stream_status in [PROOFS_SOURCE_REQUESTED, PROOFS_SENT]:
                return True

        return False

    reason = request.headers.get("HX-Prompt")

    author_mail = DirectMailUtil(
        "submissions/dormant_submission_author_notification",
        submission=submission,
        reason=reason,
    )
    author_mail.send_mail()

    if (
        submission.status == Submission.AWAITING_RESUBMISSION
        and (recommendation := submission.recommendation)
        and recommendation.is_revision
    ):
        eic_mail = DirectMailUtil(
            "submissions/dormant_submission_resubmission_editor_notification",
            submission=submission,
            revision_date=recommendation.date_submitted.strftime("%Y-%m-%d"),
        )
    elif (
        submission.status
        == Submission.ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE
    ):
        eic_mail = DirectMailUtil(
            "submissions/dormant_submission_puboffer_editor_notification",
            submission=submission,
        )
    elif submission.in_stage_in_production:
        if submission.production_stream.status == PROOFS_SOURCE_REQUESTED:
            eic_mail = DirectMailUtil(
                "submissions/dormant_submission_sourcefiles_editor_notification",
                submission=submission,
            )
        elif submission.production_stream.status == PROOFS_SENT:
            eic_mail = DirectMailUtil(
                "submissions/dormant_submission_proofssent_editor_notification",
                submission=submission,
            )

    eic_mail.send_mail()

    if submission.is_dormant:
        submission.status = infer_pre_dormant_status(submission)
        submission.visible_public = True
    elif not can_be_marked_dormant(submission):
        return HTMXResponse(
            "This Submission is not in a state where it can be marked as dormant.",
            tag="danger",
        )
    else:
        submission.status = Submission.DORMANT
        submission.visible_public = False

    submission.save()

    # Create an internal note on this submission with the reason provided through HX-Prompt
    if submission.is_dormant:
        note = Note(
            visibility=Note.VISIBILITY_INTERNAL,
            author=request.user.contributor,
            regarding_content_type=ContentType.objects.get_for_model(Submission),
            regarding_object_id=submission.id,
            title="Submission marked as dormant",
            description=reason,
        )
        note.save()

    message = "Submission has been {verb} as dormant.".format(
        verb="marked" if submission.is_dormant else "unmarked"
    )
    submission.add_event_for_edadmin(message)
    messages.success(request, message)

    return render(
        request,
        "submissions/pool/_hx_submission_details.html",
        {"submission": submission},
    )

@login_required
@fellowship_or_admin_required()
def add_remark(request, identifier_w_vn_nr):
    """Form view to add a Remark to a Submission.

    With this method, an Editorial Fellow or Board Member
    is adding a remark on a Submission.
    """
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    remark_form = RemarkForm(request.POST or None)
    if remark_form.is_valid():
        remark = Remark(
            contributor=request.user.contributor,
            submission=submission,
            remark=remark_form.cleaned_data["remark"],
        )
        remark.save()
        messages.success(request, "Your remark has succesfully been posted")
    else:
        messages.warning(request, "The form was invalidly filled.")
    return redirect(reverse("submissions:pool:pool", args=(identifier_w_vn_nr,)))


@login_required
@fellowship_required()
def assignment_request(request, assignment_id):
    """Redirect to Editorial Assignment form view.

    Exists for historical reasons; email are sent with this url construction.
    """
    assignment = get_object_or_404(
        EditorialAssignment.objects.invited(),
        to=request.user.contributor,
        pk=assignment_id,
    )
    return redirect(
        reverse(
            "submissions:pool:editorial_assignment",
            kwargs={
                "identifier_w_vn_nr": assignment.submission.preprint.identifier_w_vn_nr,
                "assignment_id": assignment.id,
            },
        )
    )


@login_required
@fellowship_required()
@transaction.atomic
def editorial_assignment(request, identifier_w_vn_nr, assignment_id=None):
    """Editorial Assignment form view."""
    submission = get_object_or_404(
        Submission.objects.seeking_assignment().in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )

    # Check if Submission is still valid for a new assignment.
    if submission.editor_in_charge:
        messages.success(
            request,
            "{} {} has already agreed to be Editor-in-charge of this Submission.".format(
                submission.editor_in_charge.profile.get_title_display(),
                submission.editor_in_charge.dbuser.last_name,
            ),
        )
        return redirect("submissions:pool:pool")
    elif submission.status == submission.ASSIGNMENT_FAILED:
        messages.success(
            request,
            (
                "Thank you for considering."
                " This Submission has failed assignment and has been rejected."
            ),
        )
        return redirect("submissions:pool:pool")

    if assignment_id:
        # Process existing EditorialAssignment.
        assignment = get_object_or_404(
            submission.editorial_assignments.invited(),
            to=request.user.contributor,
            pk=assignment_id,
        )
    else:
        # Get or create EditorialAssignment for user.
        try:
            assignment = (
                submission.editorial_assignments.invited()
                .filter(to__dbuser=request.user)
                .first()
            )
        except EditorialAssignment.DoesNotExist:
            assignment = EditorialAssignment()

    form = EditorialAssignmentForm(
        request.POST or None,
        submission=submission,
        instance=assignment,
        request=request,
    )
    if form.is_valid():
        assignment = form.save()
        if form.has_accepted_invite():
            # Fellow accepted to do a normal refereeing cycle.
            DirectMailUtil(
                "submissions/assignment_editor_notification",
                assignment=assignment,
            ).send_mail()

            if form.is_normal_cycle():
                # Inform authors about new status.
                DirectMailUtil(
                    "submissions/assignment_passed_author_notification",
                    assignment=assignment,
                ).send_mail()
            else:
                # Inform authors about new status.
                DirectMailUtil(
                    "authors/inform_authors_eic_assigned_direct_rec",
                    assignment=assignment,
                ).send_mail()

            submission.add_general_event("The Editor-in-charge has been assigned.")
            msg = "Thank you for becoming Editor-in-charge of this submission."
            url = reverse(
                "submissions:editorial_page",
                args=(submission.preprint.identifier_w_vn_nr,),
            )
        else:
            # Fellow declined the invitation.
            msg = "Thank you for considering"
            url = reverse("submissions:pool:pool")

        # Form submitted; redirect user
        messages.success(request, msg)
        return redirect(url)

    context = {
        "form": form,
        "submission": submission,
        "assignment": assignment,
    }
    return render(request, "submissions/pool/editorial_assignment.html", context)


class EICManualEICInvitationEmailView(PermissionsMixin, MailView):
    """Send a templated email to a Potential Fellow."""

    permission_required = "scipost.can_manage_college_composition"
    mail_code = "eic/manual_EIC_invitation"
    success_url = reverse_lazy("submissions:pool:pool")

    def get_queryset(self):
        """Return the fellows of this submission."""
        self.fellowship = get_object_or_404(Fellowship, pk=self.kwargs["pk"])
        self.submission = get_object_or_404(
            Submission.objects.in_pool(self.fellowship.contributor.user),
            preprint__identifier_w_vn_nr=self.kwargs["identifier_w_vn_nr"],
        )

        return self.submission.fellows.all()

    def get_mail_config(self):
        config = super().get_mail_config()

        config["fellowship"] = self.fellowship
        config["submission"] = self.submission
        config["signee_profile"] = self.request.user.contributor.profile

        return config

    def form_valid(self, form):
        self.submission.add_event_for_edadmin(
            f"A manual EIC invitation email has been sent to {self.fellowship.contributor.profile.full_name}."
        )
        return super().form_valid(form)
