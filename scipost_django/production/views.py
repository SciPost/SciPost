__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView, DeleteView

from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm, remove_perm

from finances.forms import WorkLogForm
from mails.views import MailEditorSubview

from . import constants
from .models import (
    ProductionUser,
    ProductionStream,
    ProductionEvent,
    Proofs,
    ProductionEventAttachment,
)
from .forms import (
    ProductionStreamSearchForm,
    ProductionEventForm,
    AssignOfficerForm,
    UserToOfficerForm,
    AssignSupervisorForm,
    StreamStatusForm,
    ProofsUploadForm,
    ProofsDecisionForm,
    AssignInvitationsOfficerForm,
)
from .permissions import is_production_user
from .utils import proofs_slug_to_id, ProductionUtils


################################
# 2023-05 HTMX refactoring start
################################


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def production_new(request):
    form = ProductionStreamSearchForm(user=request.user)
    context = {"search_productionstreams_form": form,}
    return render(request, "production/production_new.html", context)


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def _hx_productionstream_list(request):
    form = ProductionStreamSearchForm(request.POST or None, user=request.user)
    if form.is_valid():
        streams = form.search_results()
    else:
        streams = ProductionStream.objects.ongoing()
    paginator = Paginator(streams, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index
    context = {"count": count, "page_obj": page_obj, "start_index": start_index,}
    return render(request, "production/_hx_productionstream_list.html", context)


################################
# 2023-05 HTMX refactoring end
################################


######################
# Production process #  2023-05  ALL BELOW TO BE REFACTORED to htmx-driven views
######################


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def production(request, stream_id=None):
    """
    Overview page for the production process.
    All papers with accepted but not yet published status are included here.
    """
    streams = ProductionStream.objects.ongoing()
    if not request.user.has_perm("scipost.can_view_all_production_streams"):
        # Restrict stream queryset if user is not supervisor
        streams = streams.filter_for_user(request.user.production_user)
    streams = streams.order_by("opened")

    context = {
        "streams": streams,
    }

    if stream_id:
        try:
            # "Pre-load" ProductionStream
            context["stream"] = streams.get(id=stream_id)
            context["assign_officer_form"] = AssignOfficerForm()
            context["assign_invitiations_officer_form"] = AssignInvitationsOfficerForm()
            context["assign_supervisor_form"] = AssignSupervisorForm()
            context["prodevent_form"] = ProductionEventForm()

            if request.user.has_perm("scipost.can_view_all_production_streams"):
                types = constants.PRODUCTION_ALL_WORK_LOG_TYPES
            else:
                types = constants.PRODUCTION_OFFICERS_WORK_LOG_TYPES
            context["work_log_form"] = WorkLogForm(log_types=types)
            context["upload_proofs_form"] = ProofsUploadForm()
        except ProductionStream.DoesNotExist:
            pass

    if request.user.has_perm("scipost.can_view_timesheets"):
        context["production_team"] = ProductionUser.objects.active()

    if request.user.has_perm("scipost.can_promote_user_to_production_officer"):
        context["production_officers"] = ProductionUser.objects.active()
        context["new_officer_form"] = UserToOfficerForm()
    return render(request, "production/production.html", context)


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def completed(request):
    """
    Overview page for closed production streams.
    """
    streams = ProductionStream.objects.completed()
    if not request.user.has_perm("scipost.can_view_all_production_streams"):
        streams = streams.filter_for_user(request.user.production_user)
    streams = streams.order_by("-opened")

    context = {"streams": streams}
    return render(request, "production/completed.html", context)


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def stream(request, stream_id):
    """
    Overview page for specific stream.
    """
    streams = ProductionStream.objects.ongoing()
    if not request.user.has_perm("scipost.can_view_all_production_streams"):
        # Restrict stream queryset if user is not supervisor
        streams = streams.filter_for_user(request.user.production_user)
    stream = get_object_or_404(streams, id=stream_id)
    prodevent_form = ProductionEventForm()
    assign_officer_form = AssignOfficerForm()
    assign_invitiations_officer_form = AssignInvitationsOfficerForm()
    assign_supervisor_form = AssignSupervisorForm()
    upload_proofs_form = ProofsUploadForm()

    if request.user.has_perm("scipost.can_view_all_production_streams"):
        types = constants.PRODUCTION_ALL_WORK_LOG_TYPES
    else:
        types = constants.PRODUCTION_OFFICERS_WORK_LOG_TYPES
    work_log_form = WorkLogForm(log_types=types)
    status_form = StreamStatusForm(
        instance=stream, production_user=request.user.production_user
    )

    context = {
        "stream": stream,
        "prodevent_form": prodevent_form,
        "assign_officer_form": assign_officer_form,
        "assign_supervisor_form": assign_supervisor_form,
        "assign_invitiations_officer_form": assign_invitiations_officer_form,
        "status_form": status_form,
        "upload_proofs_form": upload_proofs_form,
        "work_log_form": work_log_form,
    }

    if request.GET.get("json"):
        return render(request, "production/_production_stream_card.html", context)
    else:
        return render(request, "production/stream.html", context)


@is_production_user()
@permission_required("scipost.can_promote_user_to_production_officer")
def user_to_officer(request):
    form = UserToOfficerForm(request.POST or None)
    if form.is_valid():
        officer = form.save()

        # Add permission group
        group = Group.objects.get(name="Production Officers")
        officer.user.groups.add(group)
        messages.success(
            request, "{user} promoted to Production Officer".format(user=officer)
        )
    return redirect(reverse("production:production"))


@is_production_user()
@permission_required("scipost.can_promote_user_to_production_officer")
def delete_officer(request, officer_id):
    production_user = get_object_or_404(ProductionUser.objects.active(), id=officer_id)
    production_user.name = "{first_name} {last_name}".format(
        first_name=production_user.user.first_name,
        last_name=production_user.user.last_name,
    )
    production_user.user = None
    production_user.save()

    messages.success(
        request, "{user} removed as Production Officer".format(user=production_user)
    )
    return redirect(reverse("production:production"))


@is_production_user()
@permission_required(
    "scipost.can_take_decisions_related_to_proofs", raise_exception=True
)
def update_status(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", stream):
        return redirect(reverse("production:production", args=(stream.id,)))

    p = request.user.production_user
    form = StreamStatusForm(request.POST or None, instance=stream, production_user=p)

    if form.is_valid():
        stream = form.save()
        messages.warning(request, "Production Stream succesfully changed status.")
    else:
        messages.warning(request, "The status change was invalid.")
    return redirect(stream.get_absolute_url())


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def add_event(request, stream_id):
    qs = ProductionStream.objects.ongoing()
    if not request.user.has_perm("scipost.can_assign_production_officer"):
        qs = qs.filter_for_user(request.user.production_user)

    stream = get_object_or_404(qs, pk=stream_id)
    prodevent_form = ProductionEventForm(request.POST or None)
    if prodevent_form.is_valid():
        prodevent = prodevent_form.save(commit=False)
        prodevent.stream = stream
        prodevent.noted_by = request.user.production_user
        prodevent.save()
        messages.success(request, "Comment added to Stream.")
    else:
        messages.warning(request, "The form was invalidly filled.")
    return redirect(reverse("production:production", args=(stream.id,)))


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def add_work_log(request, stream_id):
    stream = get_object_or_404(ProductionStream, pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", stream):
        return redirect(stream.get_absolute_url())

    if request.user.has_perm("scipost.can_view_all_production_streams"):
        types = constants.PRODUCTION_ALL_WORK_LOG_TYPES
    else:
        types = constants.PRODUCTION_OFFICERS_WORK_LOG_TYPES
    work_log_form = WorkLogForm(request.POST or None, log_types=types)

    if work_log_form.is_valid():
        log = work_log_form.save(commit=False)
        log.content = stream
        log.user = request.user
        log.save()
        messages.success(request, "Work Log added to Stream.")
    else:
        messages.warning(request, "The form was invalidly filled.")
    return redirect(stream.get_absolute_url())


@is_production_user()
@permission_required("scipost.can_assign_production_officer", raise_exception=True)
@transaction.atomic
def add_officer(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", stream):
        return redirect(reverse("production:production", args=(stream.id,)))

    form = AssignOfficerForm(request.POST or None, instance=stream)
    if form.is_valid():
        form.save()
        officer = form.cleaned_data.get("officer")
        assign_perm("can_work_for_stream", officer.user, stream)
        messages.success(
            request, "Officer {officer} has been assigned.".format(officer=officer)
        )
        event = ProductionEvent(
            stream=stream,
            event="assignment",
            comments=" tasked Production Officer with proofs production:",
            noted_to=officer,
            noted_by=request.user.production_user,
        )
        event.save()

        # Temp fix.
        # TODO: Implement proper email
        ProductionUtils.load({"request": request, "stream": stream})
        ProductionUtils.email_assigned_production_officer()
        return redirect(stream.get_absolute_url())
    else:
        for key, error in form.errors.items():
            messages.warning(request, error[0])
    return redirect(reverse("production:production", args=(stream.id,)))


@is_production_user()
@permission_required("scipost.can_assign_production_officer", raise_exception=True)
@transaction.atomic
def add_invitations_officer(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", stream):
        return redirect(reverse("production:production", args=(stream.id,)))

    form = AssignInvitationsOfficerForm(request.POST or None, instance=stream)
    if form.is_valid():
        form.save()
        officer = form.cleaned_data.get("invitations_officer")
        assign_perm("can_work_for_stream", officer.user, stream)
        messages.success(
            request,
            "Invitations Officer {officer} has been assigned.".format(officer=officer),
        )
        event = ProductionEvent(
            stream=stream,
            event="assignment",
            comments=" tasked Invitations Officer with invitations:",
            noted_to=officer,
            noted_by=request.user.production_user,
        )
        event.save()

        # Temp fix.
        # TODO: Implement proper email
        ProductionUtils.load({"request": request, "stream": stream})
        ProductionUtils.email_assigned_invitation_officer()
    else:
        for key, error in form.errors.items():
            messages.warning(request, error[0])
    return redirect(reverse("production:production", args=(stream.id,)))


@is_production_user()
@permission_required("scipost.can_assign_production_officer", raise_exception=True)
@transaction.atomic
def remove_officer(request, stream_id, officer_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", stream):
        return redirect(reverse("production:production", args=(stream.id,)))

    if getattr(stream.officer, "id", 0) == int(officer_id):
        officer = stream.officer
        stream.officer = None
        stream.save()
        if officer not in [stream.invitations_officer, stream.supervisor]:
            # Remove Officer from stream if not assigned anymore
            remove_perm("can_work_for_stream", officer.user, stream)
        messages.success(
            request, "Officer {officer} has been removed.".format(officer=officer)
        )

    return redirect(reverse("production:production", args=(stream.id,)))


@is_production_user()
@permission_required("scipost.can_assign_production_officer", raise_exception=True)
@transaction.atomic
def remove_invitations_officer(request, stream_id, officer_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", stream):
        return redirect(reverse("production:production", args=(stream.id,)))

    if getattr(stream.invitations_officer, "id", 0) == int(officer_id):
        officer = stream.invitations_officer
        stream.invitations_officer = None
        stream.save()
        if officer not in [stream.officer, stream.supervisor]:
            # Remove Officer from stream if not assigned anymore
            remove_perm("can_work_for_stream", officer.user, stream)
        messages.success(
            request,
            "Invitations Officer {officer} has been removed.".format(officer=officer),
        )

    return redirect(reverse("production:production", args=(stream.id,)))


@is_production_user()
@permission_required("scipost.can_assign_production_supervisor", raise_exception=True)
@transaction.atomic
def add_supervisor(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    form = AssignSupervisorForm(request.POST or None, instance=stream)
    if form.is_valid():
        form.save()
        supervisor = form.cleaned_data.get("supervisor")
        messages.success(
            request,
            "Supervisor {supervisor} has been assigned.".format(supervisor=supervisor),
        )
        event = ProductionEvent(
            stream=stream,
            event="assignment",
            comments=" assigned Production Supervisor:",
            noted_to=supervisor,
            noted_by=request.user.production_user,
        )
        event.save()

        assign_perm("can_work_for_stream", supervisor.user, stream)
        assign_perm("can_perform_supervisory_actions", supervisor.user, stream)

        # Temp fix.
        # TODO: Implement proper email
        ProductionUtils.load({"request": request, "stream": stream})
        ProductionUtils.email_assigned_supervisor()
        return redirect(stream.get_absolute_url())
    else:
        for key, error in form.errors.items():
            messages.warning(request, error[0])
    return redirect(reverse("production:production", args=(stream.id,)))


@is_production_user()
@permission_required("scipost.can_assign_production_supervisor", raise_exception=True)
@transaction.atomic
def remove_supervisor(request, stream_id, officer_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    if getattr(stream.supervisor, "id", 0) == int(officer_id):
        supervisor = stream.supervisor
        stream.supervisor = None
        stream.save()
        remove_perm("can_work_for_stream", supervisor.user, stream)
        remove_perm("can_perform_supervisory_actions", supervisor.user, stream)
        messages.success(
            request,
            "Supervisor {supervisor} has been removed.".format(supervisor=supervisor),
        )

    return redirect(reverse("production:production", args=(stream.id,)))


@method_decorator(is_production_user(), name="dispatch")
@method_decorator(
    permission_required("scipost.can_view_production", raise_exception=True),
    name="dispatch",
)
class UpdateEventView(UpdateView):
    model = ProductionEvent
    form_class = ProductionEventForm
    slug_field = "id"
    slug_url_kwarg = "event_id"

    def get_queryset(self):
        return self.model.objects.get_my_events(self.request.user.production_user)

    def form_valid(self, form):
        messages.success(self.request, "Event updated succesfully")
        return super().form_valid(form)


@method_decorator(is_production_user(), name="dispatch")
@method_decorator(
    permission_required("scipost.can_view_production", raise_exception=True),
    name="dispatch",
)
class DeleteEventView(DeleteView):
    model = ProductionEvent
    slug_field = "id"
    slug_url_kwarg = "event_id"

    def get_queryset(self):
        return self.model.objects.get_my_events(self.request.user.production_user)

    def form_valid(self, form):
        messages.success(self.request, "Event deleted succesfully")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


@is_production_user()
@permission_required("scipost.can_publish_accepted_submission", raise_exception=True)
@transaction.atomic
def mark_as_completed(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    stream.status = constants.PRODUCTION_STREAM_COMPLETED
    stream.closed = timezone.now()
    stream.save()

    prodevent = ProductionEvent(
        stream=stream,
        event="status",
        comments=" marked the Production Stream as completed.",
        noted_by=request.user.production_user,
    )
    prodevent.save()
    messages.success(request, "Stream marked as completed.")
    return redirect(reverse("production:production"))


@is_production_user()
@permission_required("scipost.can_upload_proofs", raise_exception=True)
@transaction.atomic
def upload_proofs(request, stream_id):
    """
    Called by a member of the Production Team.
    Upload the production version .pdf of a submission.
    """
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", stream):
        return redirect(reverse("production:production"))

    form = ProofsUploadForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        proofs = form.save(commit=False)
        proofs.stream = stream
        proofs.uploaded_by = request.user.production_user
        proofs.save()
        Proofs.objects.filter(stream=stream).exclude(version=proofs.version).exclude(
            status=constants.PROOFS_ACCEPTED
        ).update(status=constants.PROOFS_RENEWED)
        messages.success(request, "Proof uploaded.")

        # Update Stream status
        if stream.status == constants.PROOFS_TASKED:
            stream.status = constants.PROOFS_PRODUCED
            stream.save()
        elif stream.status == constants.PROOFS_RETURNED:
            stream.status = constants.PROOFS_CORRECTED
            stream.save()

        prodevent = ProductionEvent(
            stream=stream,
            event="status",
            comments="New Proofs uploaded, version {v}".format(v=proofs.version),
            noted_by=request.user.production_user,
        )
        prodevent.save()
        return redirect(stream.get_absolute_url())

    context = {"stream": stream, "form": form}
    return render(request, "production/upload_proofs.html", context)


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def proofs(request, stream_id, version):
    """
    Called by a member of the Production Team.
    Upload the production version .pdf of a submission.
    """
    stream = get_object_or_404(ProductionStream.objects.all(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", stream):
        return redirect(reverse("production:production"))

    try:
        proofs = stream.proofs.get(version=version)
    except Proofs.DoesNotExist:
        raise Http404

    context = {"stream": stream, "proofs": proofs}
    return render(request, "production/proofs.html", context)


def proofs_pdf(request, slug):
    """Open Proofs pdf."""
    if not request.user.is_authenticated:
        # Don't use the decorator but this strategy,
        # because now it will return 404 instead of a redirect to the login page.
        raise Http404

    proofs = get_object_or_404(Proofs, id=proofs_slug_to_id(slug))
    stream = proofs.stream

    # Check if user has access!
    checker = ObjectPermissionChecker(request.user)
    access = checker.has_perm("can_work_for_stream", stream) and request.user.has_perm(
        "scipost.can_view_production"
    )
    if not access and request.user.contributor:
        access = request.user.contributor in proofs.stream.submission.authors.all()
    if not access:
        raise Http404

    # Passed the test! The user may see the file!
    content_type, encoding = mimetypes.guess_type(proofs.attachment.path)
    content_type = content_type or "application/octet-stream"
    response = HttpResponse(proofs.attachment.read(), content_type=content_type)
    response["Content-Encoding"] = encoding
    return response


def production_event_attachment_pdf(request, stream_id, attachment_id):
    """Open ProductionEventAttachment pdf."""
    if not request.user.is_authenticated:
        # Don't use the decorator but this strategy,
        # because now it will return 404 instead of a redirect to the login page.
        raise Http404

    stream = get_object_or_404(ProductionStream, id=stream_id)
    attachment = get_object_or_404(
        ProductionEventAttachment.objects.filter(production_event__stream=stream),
        id=attachment_id,
    )

    # Check if user has access!
    checker = ObjectPermissionChecker(request.user)
    access = checker.has_perm("can_work_for_stream", stream) and request.user.has_perm(
        "scipost.can_view_production"
    )
    if not access and request.user.contributor:
        access = request.user.contributor in stream.submission.authors.all()
    if not access:
        raise Http404

    # Passed the test! The user may see the file!
    content_type, encoding = mimetypes.guess_type(attachment.attachment.path)
    content_type = content_type or "application/octet-stream"
    response = HttpResponse(attachment.attachment.read(), content_type=content_type)
    response["Content-Encoding"] = encoding
    return response


@login_required
@transaction.atomic
def author_decision(request, slug):
    """
    The authors of a Submission/Proof are asked for their decision on the proof.
    Accept or Decline? This will be asked if proof status is `ACCEPTED_SUP` and
    will be handled in this view.
    """
    proofs = Proofs.objects.get(id=proofs_slug_to_id(slug))
    stream = proofs.stream

    # Check if user has access!
    if request.user.contributor not in proofs.stream.submission.authors.all():
        raise Http404

    form = ProofsDecisionForm(
        request.POST or None, request.FILES or None, instance=proofs
    )
    if form.is_valid():
        proofs = form.save()
        messages.success(request, "Your decision has been sent.")

    return redirect(stream.submission.get_absolute_url())


@is_production_user()
@permission_required("scipost.can_run_proofs_by_authors", raise_exception=True)
def toggle_accessibility(request, stream_id, version):
    """
    Open/close accessibility of proofs to the authors.
    """
    stream = get_object_or_404(ProductionStream.objects.all(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", stream):
        return redirect(reverse("production:production"))

    try:
        proofs = stream.proofs.exclude(status=constants.PROOFS_UPLOADED).get(
            version=version
        )
    except Proofs.DoesNotExist:
        raise Http404

    proofs.accessible_for_authors = not proofs.accessible_for_authors
    proofs.save()
    messages.success(request, "Proofs accessibility updated.")
    return redirect(stream.get_absolute_url())


@is_production_user()
@permission_required("scipost.can_run_proofs_by_authors", raise_exception=True)
@transaction.atomic
def decision(request, stream_id, version, decision):
    """
    Send/open proofs to the authors. This decision is taken by the supervisor.
    """
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", stream):
        return redirect(reverse("production:production"))

    try:
        proofs = stream.proofs.get(version=version, status=constants.PROOFS_UPLOADED)
    except Proofs.DoesNotExist:
        raise Http404

    if decision == "accept":
        proofs.status = constants.PROOFS_ACCEPTED_SUP
        stream.status = constants.PROOFS_CHECKED
        decision = "accepted"
    else:
        proofs.status = constants.PROOFS_DECLINED_SUP
        proofs.accessible_for_authors = False
        stream.status = constants.PROOFS_TASKED
        decision = "declined"
    stream.save()
    proofs.save()

    prodevent = ProductionEvent(
        stream=stream,
        event="status",
        comments="Proofs version {version} are {decision}.".format(
            version=proofs.version, decision=decision
        ),
        noted_by=request.user.production_user,
    )
    prodevent.save()
    messages.success(request, "Proofs have been {decision}.".format(decision=decision))
    return redirect(reverse("production:proofs", args=(stream.id, proofs.version)))


@is_production_user()
@permission_required("scipost.can_run_proofs_by_authors", raise_exception=True)
@transaction.atomic
def send_proofs(request, stream_id, version):
    """
    Send/open proofs to the authors.
    """
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", stream):
        return redirect(reverse("production:production"))

    try:
        proofs = stream.proofs.can_be_send().get(version=version)
    except Proofs.DoesNotExist:
        raise Http404

    proofs.status = constants.PROOFS_SENT
    proofs.accessible_for_authors = True

    if stream.status not in [
        constants.PROOFS_PUBLISHED,
        constants.PROOFS_CITED,
        constants.PRODUCTION_STREAM_COMPLETED,
    ]:
        stream.status = constants.PROOFS_SENT
        stream.save()

    mail_request = MailEditorSubview(request, "production_send_proofs", proofs=proofs)
    if mail_request.is_valid():
        proofs.save()
        stream.save()
        messages.success(request, "Proofs have been sent.")
        mail_request.send_mail()
        prodevent = ProductionEvent(
            stream=stream,
            event="status",
            comments="Proofs version {version} sent to authors.".format(
                version=proofs.version
            ),
            noted_by=request.user.production_user,
        )
        prodevent.save()
        return redirect(stream.get_absolute_url())
    else:
        return mail_request.interrupt()

    messages.success(request, "Proofs have been sent.")
    return redirect(stream.get_absolute_url())
