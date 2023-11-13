__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from mails.views import MailView
from scipost.mixins import PermissionsMixin

from scipost.models import Remark
from scipost.forms import RemarkForm
from colleges.models import PotentialFellowship, Fellowship
from colleges.permissions import (
    fellowship_required,
    fellowship_or_admin_required,
)
from mails.utils import DirectMailUtil
from submissions.models import (
    EditorialAssignment,
    EICRecommendation,
    Submission,
)
from submissions.forms import (
    SubmissionPoolSearchForm,
    EditorialAssignmentForm,
)
from submissions.utils import SubmissionUtils


@login_required
@fellowship_or_admin_required()
def pool(request, identifier_w_vn_nr=None):
    """
    Listing of Submissions for purposes of editorial handling.
    """
    nr_potfels_to_vote_on = PotentialFellowship.objects.to_vote_on(
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
    if form.is_valid():
        submissions = form.search_results(request.user)
    else:
        submissions = Submission.objects.in_pool(request.user)[:16]
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
                submission.editor_in_charge.user.last_name,
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
                .filter(to__user=request.user)
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
            SubmissionUtils.load({"assignment": assignment})
            SubmissionUtils.send_EIC_appointment_email()

            if form.is_normal_cycle():
                # Inform authors about new status.
                SubmissionUtils.send_author_assignment_passed_email()
            else:
                # Inform authors about new status.
                mail_sender = DirectMailUtil(
                    "authors/inform_authors_eic_assigned_direct_rec",
                    assignment=assignment,
                )
                mail_sender.send_mail()

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
        config["signee"] = self.request.user.contributor.profile

        return config
