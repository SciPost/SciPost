__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from dal import autocomplete

from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.core.paginator import Paginator
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from colleges.permissions import (
    is_edadmin,
    is_edadmin_or_senior_fellow,
    is_edadmin_or_advisory_or_active_regular_or_senior_fellow,
)
from colleges.utils import check_profile_eligibility_for_fellowship
from scipost.permissions import HTMXPermissionsDenied, HTMXResponse
from submissions.models import Submission

from .constants import (
    POTENTIAL_FELLOWSHIP_STATUSES,
    POTENTIAL_FELLOWSHIP_EVENT_STATUSUPDATED,
    POTENTIAL_FELLOWSHIP_INVITED,
    POTENTIAL_FELLOWSHIP_ACTIVE_IN_COLLEGE,
    potential_fellowship_statuses_dict,
    POTENTIAL_FELLOWSHIP_EVENT_VOTED_ON,
    POTENTIAL_FELLOWSHIP_EVENT_EMAILED,
)
from .forms import (
    CollegeChoiceForm,
    FellowshipNominationSearchForm,
    FellowshipNominationVotingRoundStartForm,
    FellowshipSearchForm,
    FellowshipDynSelForm,
    FellowshipForm,
    FellowshipRemoveSubmissionForm,
    FellowshipAddSubmissionForm,
    SubmissionAddFellowshipForm,
    FellowshipRemoveProceedingsForm,
    FellowshipAddProceedingsForm,
    PotentialFellowshipForm,
    PotentialFellowshipStatusForm,
    PotentialFellowshipEventForm,
    FellowshipNominationForm,
    FellowshipNominationSearchForm,
    FellowshipNominationCommentForm,
    FellowshipNominationDecisionForm,
    FellowshipInvitationResponseForm,
)
from .models import (
    College,
    Fellowship,
    PotentialFellowship,
    PotentialFellowshipEvent,
    FellowshipNomination,
    FellowshipNominationEvent,
    FellowshipNominationVotingRound,
    FellowshipNominationVote,
    FellowshipNominationDecision,
    FellowshipInvitation,
)

from scipost.forms import EmailUsersForm, SearchTextForm
from scipost.mixins import PermissionsMixin, PaginationMixin, RequestViewMixin
from scipost.models import Contributor

from common.utils import Q_with_alternative_spellings
from mails.views import MailView, MailEditorSubviewHTMX
from ontology.models import Branch
from profiles.models import Profile
from profiles.forms import ProfileDynSelForm


class CollegeListView(ListView):
    model = College

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["branches"] = Branch.objects.all()
        return context


class CollegeDetailView(DetailView):
    model = College
    template_name = "colleges/college_detail.html"

    def get_object(self, queryset=None):
        """
        Bypass django.views.generic.detail.SingleObjectMixin:
        since CollegeSlugConverter already found the College as a kwarg, just pass that object on.
        """
        return self.kwargs["college"]


class FellowshipAutocompleteView(autocomplete.Select2QuerySetView):
    """
    View to feed the Select2 widget.
    """

    def get_queryset(self):
        qs = Fellowship.objects.all()
        if self.q:
            qs = qs.filter(
                Q(contributor__profile__first_name__icontains=self.q)
                | Q(contributor__profile__last_name__icontains=self.q)
            ).distinct()
        return qs


class FellowshipCreateView(PermissionsMixin, CreateView):
    """
    Create a new Fellowship instance for an existing Contributor.

    A new Fellowship can be created only for:
    * an existing Fellow who is renewed
    * out of an existing PotentialFellowship (elected, or named by Admin)

    If the elected/named Fellow does not yet have a Contributor object,
    this must be set up first.
    """

    permission_required = "scipost.can_manage_college_composition"
    form_class = FellowshipForm
    template_name = "colleges/fellowship_form.html"

    def get_initial(self):
        initial = super().get_initial()
        contributor = get_object_or_404(
            Contributor, pk=self.kwargs.get("contributor_id")
        )
        initial.update(
            {
                "contributor": contributor.id,
                "start_date": datetime.date.today(),
                "until_date": datetime.date.today()
                + datetime.timedelta(days=int(5 * 365.25)),
            }
        )
        return initial

    def form_valid(self, form):
        """
        Save the new Fellowship, add College rights and update the status of any PotentialFellowship and FellowshipNomination.
        """
        self.object = form.save()
        group = Group.objects.get(name="Editorial College")
        self.object.contributor.user.groups.add(group)
        potfels = PotentialFellowship.objects.filter(
            profile=self.object.contributor.profile
        )
        for potfel in potfels:
            potfelevent = PotentialFellowshipEvent(
                potfel=potfel,
                event=POTENTIAL_FELLOWSHIP_EVENT_STATUSUPDATED,
                comments="Fellowship created for this Potential Fellow",
                noted_on=timezone.now(),
                noted_by=self.request.user.contributor,
            )
            potfelevent.save()
            potfel.status = POTENTIAL_FELLOWSHIP_ACTIVE_IN_COLLEGE
            potfel.save()
        nomination = FellowshipNomination.objects.filter(
            profile=self.object.contributor.profile
        ).first()
        if nomination:
            nomination.fellowship = self.object
            nomination.save()
            nomination.add_event(
                description="Fellowship created",
                by=self.request.user.contributor,
            )
        return redirect(self.get_success_url())


class FellowshipUpdateView(PermissionsMixin, UpdateView):
    """
    Update an existing Fellowship.
    """

    permission_required = "scipost.can_manage_college_composition"
    model = Fellowship
    form_class = FellowshipForm
    template_name = "colleges/fellowship_form.html"


class FellowshipDetailView(PermissionsMixin, DetailView):
    permission_required = "scipost.can_manage_college_composition"
    model = Fellowship

    def get_queryset(self):
        queryset = Fellowship.objects.all().prefetch_related(
            "pool__preprint",
            "pool__editor_in_charge",
        )
        return queryset


class FellowshipListView(PermissionsMixin, PaginationMixin, ListView):
    """
    List Fellowship instances (accessible to College managers).
    """

    permission_required = "scipost.can_manage_college_composition"
    model = Fellowship
    paginate_by = 25

    def get_queryset(self):
        """
        Return a queryset of Fellowships filtered by optional GET data.
        """
        queryset = Fellowship.objects.all()
        if self.kwargs.get("acad_field", None):
            queryset = queryset.filter(
                contributor__profile__acad_field=self.kwargs["acad_field"]
            )
            if self.kwargs.get("specialty", None):
                queryset = queryset.filter(
                    contributor__profile__specialties=self.kwargs["specialty"]
                )
        if self.request.GET.get("type", None):
            if self.request.GET.get("type") == "regular":
                queryset = queryset.filter(guest=False)
            elif self.request.GET.get("type") == "guest":
                queryset = queryset.filter(guest=True)
        if self.request.GET.get("text"):
            query = Q_with_alternative_spellings(
                contributor__profile__last_name__istartswith=self.request.GET["text"]
            )
            queryset = queryset.filter(query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["searchform"] = SearchTextForm(
            initial={"text": self.request.GET.get("text")}
        )
        return context


@permission_required("scipost.can_draft_publication")
def _hx_fellowship_dynsel_list(request):
    form = FellowshipDynSelForm(request.POST or None)
    if form.is_valid():
        fellowships = form.search_results()
    else:
        fellowships = Fellowship.objects.none()
    context = {
        "fellowships": fellowships,
        "action_url_name": form.cleaned_data["action_url_name"],
        "action_url_base_kwargs": form.cleaned_data["action_url_base_kwargs"],
        "action_target_element_id": form.cleaned_data["action_target_element_id"],
    }
    return render(request, "colleges/_hx_fellowship_dynsel_list.html", context)


class FellowshipStartEmailView(PermissionsMixin, MailView):
    """
    After setting up a new Fellowship, send an info email to the new Fellow.
    """

    permission_required = "scipost.can_manage_college_composition"
    queryset = Fellowship.objects.all()
    mail_code = "fellows/email_fellow_fellowship_start"
    success_url = reverse_lazy("colleges:fellowships")


@login_required
@permission_required("scipost.can_manage_college_composition", raise_exception=True)
def email_College_Fellows(request, college):
    """
    Send an email to all Fellows within a College.
    """
    user_ids = [
        f.contributor.user.id for f in college.fellowships.regular_or_senior().active()
    ]
    form = EmailUsersForm(request.POST or None, initial={"users": user_ids})
    if form.is_valid():
        form.save()
        messages.success(request, "Email sent")
        return redirect(college.get_absolute_url())
    return render(
        request,
        "colleges/email_College_Fellows.html",
        {"form": form, "college": college},
    )


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def _hx_submission_add_fellowship(request, identifier_w_vn_nr):
    """Add Fellowship to a Submission's Fellowship."""
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    form = SubmissionAddFellowshipForm(request.POST or None, instance=submission)

    if form.is_valid():
        form.save()
        messages.success(
            request,
            "Fellowship {fellowship} ({id}) added to Submission.".format(
                fellowship=form.cleaned_data["fellowship"].contributor,
                id=form.cleaned_data["fellowship"].id,
            ),
        )
        return render(
            request,
            "submissions/pool/_submission_fellows.html",
            context={
                "submission": submission,
            },
        )
    context = {
        "submission": submission,
        "form": form,
    }
    return render(request, "colleges/_hx_submission_add_fellowship.html", context)


@login_required
@user_passes_test(is_edadmin)
def _hx_submission_remove_fellowship(request, identifier_w_vn_nr, pk):
    """Remove Fellowship from a Submission's Fellowship."""
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    submission.fellows.remove(pk)
    return render(
        request,
        "submissions/pool/_submission_fellows.html",
        context={
            "submission": submission,
        },
    )


@login_required
@permission_required("scipost.can_manage_college_composition", raise_exception=True)
def fellowship_remove_submission(request, id, identifier_w_vn_nr):
    """Remove Submission from the Fellowship."""
    fellowship = get_object_or_404(Fellowship, id=id)
    submission = get_object_or_404(
        fellowship.pool.all(), preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    form = FellowshipRemoveSubmissionForm(
        request.POST or None, submission=submission, instance=fellowship
    )

    if form.is_valid() and request.POST:
        form.save()
        messages.success(
            request,
            "Submission {submission_id} removed from Fellowship.".format(
                submission_id=identifier_w_vn_nr
            ),
        )
        return redirect(fellowship.get_absolute_url())

    context = {"fellowship": fellowship, "form": form, "submission": submission}
    return render(request, "colleges/fellowship_submission_remove.html", context)


@login_required
@permission_required("scipost.can_manage_college_composition", raise_exception=True)
def fellowship_add_submission(request, id):
    """Add Submission to the pool of a Fellowship."""
    fellowship = get_object_or_404(Fellowship, id=id)
    form = FellowshipAddSubmissionForm(request.POST or None, instance=fellowship)

    if form.is_valid():
        form.save()
        messages.success(
            request,
            "Submission {submission_id} added to Fellowship.".format(
                submission_id=form.cleaned_data[
                    "submission"
                ].preprint.identifier_w_vn_nr
            ),
        )
        return redirect(fellowship.get_absolute_url())

    context = {
        "fellowship": fellowship,
        "form": form,
    }
    return render(request, "colleges/fellowship_submission_add.html", context)


@login_required
@permission_required("scipost.can_manage_college_composition", raise_exception=True)
def fellowship_remove_proceedings(request, id, proceedings_id):
    """
    Remove Proceedings from the pool of a Fellowship.
    """
    fellowship = get_object_or_404(Fellowship, id=id)
    proceedings = get_object_or_404(fellowship.proceedings.all(), id=proceedings_id)
    form = FellowshipRemoveProceedingsForm(
        request.POST or None, proceedings=proceedings, instance=fellowship
    )

    if form.is_valid() and request.POST:
        form.save()
        messages.success(
            request, "Proceedings %s removed from Fellowship." % str(proceedings)
        )
        return redirect(fellowship.get_absolute_url())

    context = {"fellowship": fellowship, "form": form, "proceedings": proceedings}
    return render(request, "colleges/fellowship_proceedings_remove.html", context)


@login_required
@permission_required("scipost.can_manage_college_composition", raise_exception=True)
def fellowship_add_proceedings(request, id):
    """
    Add Proceedings to the pool of a Fellowship.
    """
    fellowship = get_object_or_404(Fellowship, id=id)
    form = FellowshipAddProceedingsForm(request.POST or None, instance=fellowship)

    if form.is_valid():
        form.save()
        proceedings = form.cleaned_data.get("proceedings", "")
        messages.success(
            request, "Proceedings %s added to Fellowship." % str(proceedings)
        )
        return redirect(fellowship.get_absolute_url())

    context = {
        "fellowship": fellowship,
        "form": form,
    }
    return render(request, "colleges/fellowship_proceedings_add.html", context)


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def fellowships_monitor(request):
    """
    Dashboard providing an overview of Fellows' activity levels (forlevels of activity. EdAdmin and SF).
    """
    context = {
        "college_choice_form": CollegeChoiceForm(),
    }
    return render(request, "colleges/fellowships_monitor.html", context)


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def _hx_fellowships_monitor_college_choice(request):
    if request.method == "POST":
        form = CollegeChoiceForm(request.POST)
        if form.is_valid():
            fellowships_search_form = FellowshipSearchForm(
                initial={"college": form.cleaned_data["college"]},
            )
            context = {
                "fellowships_search_form": fellowships_search_form,
            }
            return render(request, "colleges/_hx_fellowships_search_form.html", context)


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def _hx_fellowships_monitor(request):
    if request.method == "POST":
        form = FellowshipSearchForm(request.POST)
        if form.is_valid():
            fellowships = form.search_results()
        else:
            fellowships = Fellowship.objects.active()
        paginator = Paginator(fellowships, 16)
        page_nr = request.GET.get("page")
        page_obj = paginator.get_page(page_nr)
        context = {"page_obj": page_obj}
        return render(request, "colleges/_hx_fellowships_monitor.html", context)


#########################
# Potential Fellowships #
#########################


class PotentialFellowshipCreateView(PermissionsMixin, RequestViewMixin, CreateView):
    """
    Formview to create a new Potential Fellowship.
    """

    permission_required = "scipost.can_add_potentialfellowship"
    form_class = PotentialFellowshipForm
    template_name = "colleges/potentialfellowship_form.html"
    success_url = reverse_lazy("colleges:potential_fellowships")


class PotentialFellowshipUpdateView(PermissionsMixin, RequestViewMixin, UpdateView):
    """
    Formview to update a Potential Fellowship.
    """

    permission_required = "scipost.can_manage_college_composition"
    model = PotentialFellowship
    form_class = PotentialFellowshipForm
    template_name = "colleges/potentialfellowship_form.html"
    success_url = reverse_lazy("colleges:potential_fellowships")


class PotentialFellowshipUpdateStatusView(PermissionsMixin, UpdateView):
    """
    Formview to update the status of a Potential Fellowship.
    """

    permission_required = "scipost.can_manage_college_composition"
    model = PotentialFellowship
    fields = ["status"]
    success_url = reverse_lazy("colleges:potential_fellowships")

    def form_valid(self, form):
        event = PotentialFellowshipEvent(
            potfel=self.object,
            event=POTENTIAL_FELLOWSHIP_EVENT_STATUSUPDATED,
            comments=(
                "Status updated to %s"
                % potential_fellowship_statuses_dict[form.cleaned_data["status"]]
            ),
            noted_on=timezone.now(),
            noted_by=self.request.user.contributor,
        )
        event.save()
        return super().form_valid(form)


class PotentialFellowshipDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a Potential Fellowship.
    """

    permission_required = "scipost.can_manage_college_composition"
    model = PotentialFellowship
    success_url = reverse_lazy("colleges:potential_fellowships")


class PotentialFellowshipListView(PermissionsMixin, PaginationMixin, ListView):
    """
    List the PotentialFellowship object instances.
    """

    permission_required = "scipost.can_view_potentialfellowship_list"
    model = PotentialFellowship
    paginate_by = 25

    def get_queryset(self):
        """
        Return a queryset of PotentialFellowships using optional GET data.
        """
        queryset = PotentialFellowship.objects.all()
        # Admin and EdAdmin see all
        # while Advisory Board and (Senior) Fellows see their field by default
        # if they have not specified another field
        acad_field = None
        if not (
            self.request.user.contributor.is_scipost_admin
            or self.request.user.contributor.is_ed_admin
        ):
            acad_field = self.request.user.contributor.profile.acad_field
        acad_field = self.kwargs.get("acad_field", None) or acad_field
        if acad_field:
            queryset = queryset.filter(profile__acad_field=acad_field)
            if self.kwargs.get("specialty", None):
                queryset = queryset.filter(
                    profile__specialties=self.kwargs["specialty"]
                )
        if self.request.GET.get("status", None):
            queryset = queryset.filter(status=self.request.GET.get("status"))
        if self.request.GET.get("text"):
            query = Q_with_alternative_spellings(
                profile__last_name__istartswith=self.request.GET["text"]
            )
            queryset = queryset.filter(query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["potfels_to_vote_on"] = PotentialFellowship.objects.to_vote_on(
            self.request.user.contributor
        )
        context["potfels_voted_on"] = PotentialFellowship.objects.voted_on(
            self.request.user.contributor
        )
        context["statuses"] = POTENTIAL_FELLOWSHIP_STATUSES
        context["searchform"] = SearchTextForm(
            initial={"text": self.request.GET.get("text")}
        )
        return context


class PotentialFellowshipDetailView(PermissionsMixin, DetailView):
    permission_required = "scipost.can_view_potentialfellowship_list"
    model = PotentialFellowship

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["pfstatus_form"] = PotentialFellowshipStatusForm(
            initial={"status": self.object.status}
        )
        context["pfevent_form"] = PotentialFellowshipEventForm()
        return context


@login_required
@permission_required("scipost.can_vote_on_potentialfellowship", raise_exception=True)
def vote_on_potential_fellowship(request, potfel_id, vote):
    potfel = get_object_or_404(PotentialFellowship, pk=potfel_id)
    if not potfel.can_vote(request.user):
        raise Http404
    potfel.in_agreement.remove(request.user.contributor)
    potfel.in_abstain.remove(request.user.contributor)
    potfel.in_disagreement.remove(request.user.contributor)
    if vote == "A":
        potfel.in_agreement.add(request.user.contributor)
        comments = "Voted Agree"
    elif vote == "N":
        potfel.in_abstain.add(request.user.contributor)
        comments = "Voted Abstain"
    elif vote == "D":
        potfel.in_disagreement.add(request.user.contributor)
        comments = "Voted Disagree"
    else:
        raise Http404
    newevent = PotentialFellowshipEvent(
        potfel=potfel,
        event=POTENTIAL_FELLOWSHIP_EVENT_VOTED_ON,
        comments=comments,
        noted_by=request.user.contributor,
    )
    newevent.save()
    return redirect(reverse("colleges:potential_fellowships"))


class PotentialFellowshipInitialEmailView(PermissionsMixin, MailView):
    """Send a templated email to a Potential Fellow."""

    permission_required = "scipost.can_manage_college_composition"
    queryset = PotentialFellowship.objects.all()
    mail_code = "potentialfellowships/invite_potential_fellow_initial"
    success_url = reverse_lazy("colleges:potential_fellowships")

    def form_valid(self, form):
        """Create an event associated to this outgoing email."""
        event = PotentialFellowshipEvent(
            potfel=self.object,
            event=POTENTIAL_FELLOWSHIP_EVENT_EMAILED,
            comments="Emailed initial template to potential Fellow",
            noted_on=timezone.now(),
            noted_by=self.request.user.contributor,
        )
        event.save()
        self.object.status = POTENTIAL_FELLOWSHIP_INVITED
        self.object.save()
        return super().form_valid(form)


class PotentialFellowshipEventCreateView(PermissionsMixin, CreateView):
    """
    Add an event for a Potential Fellowship.
    """

    permission_required = "scipost.can_manage_college_composition"
    form_class = PotentialFellowshipEventForm
    success_url = reverse_lazy("colleges:potential_fellowships")

    def form_valid(self, form):
        form.instance.potfel = get_object_or_404(
            PotentialFellowship, id=self.kwargs["pk"]
        )
        form.instance.noted_on = timezone.now()
        form.instance.noted_by = self.request.user.contributor
        messages.success(self.request, "Event added successfully")
        return super().form_valid(form)


###############
# Nominations #
###############


@login_required
@user_passes_test(is_edadmin_or_advisory_or_active_regular_or_senior_fellow)
def nominations(request):
    """
    List Nominations.
    """
    context = {}
    return render(request, "colleges/nominations.html", context)


@login_required
@user_passes_test(is_edadmin_or_advisory_or_active_regular_or_senior_fellow)
def _hx_nomination_form(request, profile_id):
    profile = get_object_or_404(Profile, pk=profile_id)
    failed_eligibility_criteria = check_profile_eligibility_for_fellowship(profile)
    if failed_eligibility_criteria:
        return render(
            request,
            "colleges/_hx_failed_eligibility_criteria.html",
            {
                "profile": profile,
                "failed_eligibility_criteria": failed_eligibility_criteria,
            },
        )
    nomination_form = FellowshipNominationForm(request.POST or None, profile=profile)
    if nomination_form.is_valid():
        nomination = nomination_form.save()
        nomination.add_event(description="Nominated", by=request.user.contributor)
        return HTMXResponse(
            f"{nomination.profile} successfully nominated to {nomination.college}.",
            tag="success",
        )
    nomination_form.fields["nominated_by"].initial = request.user.contributor
    context = {
        "profile": profile,
        "nomination_form": nomination_form,
    }
    return render(request, "colleges/_hx_nomination_form.html", context)


def _hx_nomination_round_remove_voter(request, round_id, voter_id):
    """Remove a voter from a nomination's voting round."""
    round = get_object_or_404(FellowshipNominationVotingRound, pk=round_id)

    voter = get_object_or_404(Fellowship, pk=voter_id)
    if voter in round.eligible_to_vote.all():
        round.eligible_to_vote.remove(voter)
        round.save()
        messages.success(
            request, f"Removed {voter} from the voters list of this round."
        )
    else:
        messages.error(request, f"{voter} was not in the voters list of this round.")
    return HttpResponse("")


@login_required
@user_passes_test(is_edadmin_or_advisory_or_active_regular_or_senior_fellow)
def _hx_nomination_details_contents(request, nomination_id):
    """For (re)loading the details if modified."""
    nomination = get_object_or_404(FellowshipNomination, pk=nomination_id)
    context = {
        "nomination": nomination,
    }
    return render(request, "colleges/_hx_nomination_details_contents.html", context)


@login_required
@user_passes_test(is_edadmin_or_advisory_or_active_regular_or_senior_fellow)
def _hx_voting_round_summary(request, round_id):
    """For (re)loading the round summary if modified."""
    round = get_object_or_404(FellowshipNominationVotingRound, pk=round_id)
    context = {
        "round": round,
    }
    return render(request, "colleges/_hx_voting_round_summary.html", context)


def _hx_nominations_search_form(request, filter_set: str):
    form = FellowshipNominationSearchForm(
        user=request.user,
        session_key=request.session.session_key,
    )

    if filter_set == "empty":
        form.apply_filter_set({}, none_on_empty=True)

    context = {
        "form": form,
    }
    return render(request, "colleges/_hx_nominations_search_form.html", context)


def _hx_nominations_list(request):
    form = FellowshipNominationSearchForm(
        request.POST or None, user=request.user, session_key=request.session.session_key
    )
    if form.is_valid():
        nominations = form.search_results()
    else:
        nominations = FellowshipNomination.objects.all()
    paginator = Paginator(nominations, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index
    context = {
        "count": count,
        "page_obj": page_obj,
        "start_index": start_index,
    }
    return render(request, "colleges/_hx_nominations_list.html", context)


def _hx_nomination_voting_rounds_tab(request, nomination_id, round_id):
    """Render the selected voting round contents and display the others as tabs."""
    nomination = get_object_or_404(FellowshipNomination, pk=nomination_id)
    voting_rounds = nomination.voting_rounds.all().order_by("-voting_opens")

    inaccessible_round_ids = [
        round.id for round in voting_rounds if not round.can_view(request.user)
    ]

    should_show_new_round_tab_btn = request.user.contributor.is_ed_admin and (
        nomination.voting_rounds.count() == 0
        or (
            nomination.latest_voting_round.is_closed
            and (decision := getattr(nomination.latest_voting_round, "decision", None))
            and not decision.outcome == FellowshipNominationDecision.OUTCOME_ELECTED
        )
    )

    context = {
        "nomination": nomination,
        "voting_rounds": voting_rounds,
        "inaccessible_round_ids": inaccessible_round_ids,
        "should_show_new_round_tab_btn": should_show_new_round_tab_btn,
    }

    if round_id != 0:
        selected_round = voting_rounds.get(id=round_id)
        context["selected_round"] = selected_round

    return render(request, "colleges/_hx_nomination_voting_rounds_tab.html", context)


@login_required
@user_passes_test(is_edadmin)
def _hx_nomination_voting_rounds_create(request, nomination_id):
    nomination = get_object_or_404(FellowshipNomination, pk=nomination_id)
    new_round = FellowshipNominationVotingRound(
        nomination=nomination, voting_opens=None, voting_deadline=None
    )
    new_round.save()
    _ = _hx_nomination_round_add_eligible_voter_set(
        request, new_round.id, "with_specialty_overlap"
    )

    return _hx_nomination_voting_rounds_tab(request, nomination_id, new_round.id)


@login_required
@user_passes_test(is_edadmin_or_advisory_or_active_regular_or_senior_fellow)
def _hx_nomination_comments(request, nomination_id):
    nomination = get_object_or_404(FellowshipNomination, pk=nomination_id)
    initial = {
        "nomination": nomination,
        "by": request.user.contributor,
    }
    form = FellowshipNominationCommentForm(request.POST or None, initial=initial)
    if form.is_valid():
        form.save()
        nomination.add_event(description="Comment added", by=request.user.contributor)
        form = FellowshipNominationCommentForm(initial=initial)
    context = {
        "nomination": nomination,
        "form": form,
    }
    return render(request, "colleges/_hx_nomination_comments.html", context)


@login_required
@user_passes_test(is_edadmin_or_advisory_or_active_regular_or_senior_fellow)
def _hx_nomination_vote(request, round_id):
    fellowship = request.user.contributor.session_fellowship(request)
    voting_round = get_object_or_404(
        FellowshipNominationVotingRound,
        pk=round_id,
        eligible_to_vote=fellowship,
    )

    # Check if the voting round is still open
    if not voting_round.is_open:
        return HTMXResponse(
            """You cannot vote in non-open rounds.""",
            tag="danger",
        )
    if request.method == "POST":
        vote_object, created = FellowshipNominationVote.objects.update_or_create(
            voting_round=voting_round,
            fellow=fellowship,
            defaults={
                "vote": request.POST.get("vote"),
                "on": timezone.now(),
            },
        )
        if created:
            voting_round.nomination.add_event(
                description="Vote received",
                by=request.user.contributor,
            )
        else:
            voting_round.nomination.add_event(
                description="Vote updated",
                by=request.user.contributor,
            )
    else:
        vote_object = FellowshipNominationVote.objects.filter(
            voting_round=voting_round,
            fellow=fellowship,
        ).first()
    context = {
        "voting_round": voting_round,
        "vote_object": vote_object,
        "VOTE_BS_CLASSES": FellowshipNominationVote.VOTE_BS_CLASSES,
    }
    return render(request, "colleges/_hx_nomination_vote.html", context)


@login_required
@user_passes_test(is_edadmin)
def _hx_voting_round_start_form(request, round_id):
    round = get_object_or_404(FellowshipNominationVotingRound, pk=round_id)
    form = FellowshipNominationVotingRoundStartForm(
        request.POST or None,
        instance=round,
    )
    if form.is_valid():
        form.save()
        messages.success(
            request,
            f"Voting round for {round.nomination.profile} started "
            f"from {round.voting_opens} until {round.voting_deadline}.",
        )

    return render(
        request,
        "colleges/_hx_voting_round_start_form.html",
        {"form": form, "round": round},
    )


@login_required
@user_passes_test(is_edadmin)
def _hx_nomination_decision_form(request, round_id):
    voting_round = get_object_or_404(FellowshipNominationVotingRound, pk=round_id)
    nomination = voting_round.nomination
    decision_form = FellowshipNominationDecisionForm(
        request.POST or None, voting_round=voting_round
    )
    if decision_form.is_valid():
        decision = decision_form.save()
        nomination.add_event(description="Decision fixed", by=request.user.contributor)
        if decision.outcome == FellowshipNominationDecision.OUTCOME_ELECTED:
            invitation = FellowshipInvitation(
                nomination=nomination,
                response=FellowshipInvitation.RESPONSE_NOT_YET_INVITED,
            )
            invitation.save()
            nomination.add_event(
                description="Invitation created", by=request.user.contributor
            )
    context = {
        "voting_round": voting_round,
        "decision_form": decision_form,
    }
    return render(request, "colleges/_hx_nomination_decision_form.html", context)


# Check permission to create a new nomination
def _hx_nomination_new(request):
    """Render the contents of the new nomination form."""
    profile_dynsel_form = ProfileDynSelForm(
        initial={
            "action_url_name": "colleges:_hx_nomination_form",
            "action_url_base_kwargs": {},
            "action_target_element_id": "nomination_form_response",
            "action_target_swap": "innerHTML",
        }
    )
    context = {
        "profile_dynsel_form": profile_dynsel_form,
    }

    return render(request, "colleges/_hx_nomination_new.html", context)


class FellowshipInvitationEmailInitialView(PermissionsMixin, MailView):
    """Send a templated email to an elected nominee."""

    permission_required = "scipost.can_manage_college_composition"
    queryset = FellowshipInvitation.objects.all()
    mail_code = "fellowship_nominees/fellowship_invitation_initial"
    success_url = reverse_lazy("colleges:nominations")

    def form_valid(self, form):
        """Create an event associated to this outgoing email."""
        self.object.nomination.add_event(
            description="Initial invitation email sent",
            by=self.request.user.contributor,
        )
        self.object.invited_on = timezone.now()
        self.object.response = FellowshipInvitation.RESPONSE_INVITED
        self.object.save()
        return super().form_valid(form)


@login_required
@user_passes_test(is_edadmin)
def _hx_fellowship_invitation_update_response(request, invitation_id):
    invitation = get_object_or_404(FellowshipInvitation, pk=invitation_id)
    form = FellowshipInvitationResponseForm(
        request.POST or None,
        instance=invitation,
    )
    if form.is_valid():
        invitation = form.save()
        invitation.nomination.add_event(
            description=f"Response updated to: {invitation.get_response_display()}",
            by=request.user.contributor,
        )

        nonexpired_fellowship = (
            Fellowship.objects.exclude(
                until_date__lte=timezone.now().date(),
            )
            .filter(
                college=invitation.nomination.college,
                contributor=invitation.nomination.profile.contributor,
            )
            .order_by("-start_date")
            .first()
        )

        # If the invitation is accepted or postponed, create a Fellowship
        if invitation.response in [
            FellowshipInvitation.RESPONSE_ACCEPTED,
            FellowshipInvitation.RESPONSE_POSTPONED,
        ]:
            # Create a new Fellowship if no object exists
            if not nonexpired_fellowship:
                fellowship = Fellowship.objects.create(
                    college=invitation.nomination.college,
                    contributor=invitation.nomination.profile.contributor,
                    start_date=timezone.now()
                    if invitation.response == FellowshipInvitation.RESPONSE_ACCEPTED
                    else invitation.postpone_start_to,
                    until_date=None,
                )

                invitation.nomination.add_event(
                    description=f"Fellowship created (start: {fellowship.start_date.strftime('%Y-%m-%d')})",
                    by=request.user.contributor,
                )
            else:
                # Update the start date of the Fellowship if an object already exists
                nonexpired_fellowship.start_date = (
                    timezone.now()
                    if invitation.response == FellowshipInvitation.RESPONSE_ACCEPTED
                    else invitation.postpone_start_to
                )
                nonexpired_fellowship.until_date = None
                invitation.nomination.add_event(
                    description=f"Fellowship start date updated (start: {nonexpired_fellowship.start_date.strftime('%Y-%m-%d')})",
                    by=request.user.contributor,
                )
                nonexpired_fellowship.save()
        # Terminate the Fellowship if the invitation is declined
        elif invitation.response == FellowshipInvitation.RESPONSE_DECLINED:
            if nonexpired_fellowship:
                nonexpired_fellowship.until_date = (
                    timezone.now().date()
                    if nonexpired_fellowship.is_active()
                    else nonexpired_fellowship.start_date
                )
                invitation.nomination.add_event(
                    description=f"Fellowship ended (end: {nonexpired_fellowship.until_date.strftime('%Y-%m-%d')})",
                    by=request.user.contributor,
                )
                nonexpired_fellowship.save()

        return HTMXResponse(
            f"Response updated to: {invitation.get_response_display()}",
            tag="success",
        )
    context = {
        "invitation": invitation,
        "form": form,
    }
    return render(
        request,
        "colleges/_hx_nomination_invitation_update_response.html",
        context,
    )


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def _hx_nomination_voter_table(request, round_id):
    round = get_object_or_404(FellowshipNominationVotingRound, pk=round_id)
    voters = round.eligible_to_vote.all()
    nominee_specialties = round.nomination.profile.specialties.all()

    for voter in voters:
        voter.vote = round.votes.filter(fellow=voter).first()

    context = {
        "voters": voters,
        "round": round,
        "nominee_specialties": nominee_specialties,
    }
    return render(request, "colleges/_hx_nomination_voter_table.html", context)


@login_required
@user_passes_test(is_edadmin)
def _hx_nomination_round_eligible_voter_action(
    request, round_id, fellowship_id, action
):
    round = get_object_or_404(FellowshipNominationVotingRound, pk=round_id)
    fellowship = get_object_or_404(Fellowship, pk=fellowship_id)

    if action == "add":
        print(round.nomination.profile)
        if round.nomination.profile.has_competing_interest_with(
            fellowship.contributor.profile
        ):
            messages.error(
                request,
                f"{fellowship} has a competing interest with the nominee and cannot be added to the voters list.",
            )
        else:
            round.eligible_to_vote.add(fellowship)
    if action == "remove":
        round.eligible_to_vote.remove(fellowship)
    return redirect(
        reverse("colleges:_hx_nomination_voter_table", kwargs={"round_id": round.id})
    )


@login_required
@user_passes_test(is_edadmin)
def _hx_nomination_round_add_eligible_voter_set(request, round_id, voter_set_name):
    round = get_object_or_404(FellowshipNominationVotingRound, pk=round_id)

    voter_set = Fellowship.objects.none()

    senior_active_fellows = (
        Fellowship.objects.active()
        .no_competing_interests_with(round.nomination.profile)
        .senior()
    )

    if voter_set_name == "with_specialty_overlap":
        specialties_slug_list = [
            s.slug for s in round.nomination.profile.specialties.all()
        ]
        voter_set = senior_active_fellows.specialties_overlap(specialties_slug_list)
    elif voter_set_name == "all_seniors":
        voter_set = senior_active_fellows.filter(college=round.nomination.college)

    round.eligible_to_vote.add(*voter_set.distinct())
    return redirect(
        reverse("colleges:_hx_nomination_voter_table", kwargs={"round_id": round.id})
    )


def _hx_voting_round_details(request, round_id):
    round = get_object_or_404(FellowshipNominationVotingRound, pk=round_id)
    context = {
        "round": round,
    }

    if not round.can_view(request.user):
        return HTMXResponse(
            "You are not allowed to vote in this round. ",
            # "This may be because you are not a senior Fellow of the College "
            # "or because you may not have been invited to vote in it.",
            tag="danger",
        )

    if not round.is_closed:
        voter_add_form = FellowshipDynSelForm(
            initial={
                "action_url_name": "colleges:_hx_nomination_round_eligible_voter_action",
                "action_url_base_kwargs": {"round_id": round_id, "action": "add"},
                "action_target_element_id": f"nomination-{round.nomination.id}-round-{round_id}-voters",
                "action_target_swap": "innerHTML",
            }
        )
        context["voter_add_form"] = voter_add_form

    return render(request, "colleges/_hx_voting_round_details.html", context)
