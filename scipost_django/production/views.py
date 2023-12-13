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
from mails.views import MailEditorSubviewHTMX
from scipost.permissions import (
    HTMXPermissionsDenied,
    HTMXResponse,
    permission_required_htmx,
)

from . import constants
from .models import (
    ProductionUser,
    ProductionStream,
    ProductionEvent,
    Proofs,
    ProductionEventAttachment,
)
from .forms import (
    BulkAssignOfficersForm,
    ProductionStreamSearchForm,
    ProductionEventForm,
    ProductionEventForm_deprec,
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
def production(request):
    search_productionstreams_form = ProductionStreamSearchForm(
        user=request.user, session_key=request.session.session_key
    )
    bulk_assign_officer_form = BulkAssignOfficersForm()
    context = {
        "search_productionstreams_form": search_productionstreams_form,
        "bulk_assign_officer_form": bulk_assign_officer_form,
    }
    return render(request, "production/production.html", context)


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def _hx_productionstream_list(request):
    form = ProductionStreamSearchForm(
        request.POST or None, user=request.user, session_key=request.session.session_key
    )
    if form.is_valid():
        streams = form.search_results()
    else:
        streams = ProductionStream.objects.ongoing()
    paginator = Paginator(streams, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index
    context = {
        "count": count,
        "page_obj": page_obj,
        "start_index": start_index,
    }
    return render(request, "production/_hx_productionstream_list.html", context)


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def _hx_productionstream_details_contents(request, productionstream_id):
    productionstream = get_object_or_404(ProductionStream, pk=productionstream_id)

    # Determine which accordion tab to open by default
    accordion_default_open = ""

    if request.user.has_perm("scipost.can_assign_production_supervisor"):
        accordion_default_open = "change-properties"

    if request.user.production_user == productionstream.supervisor:
        if productionstream.status in [
            constants.PROOFS_ACCEPTED,
        ]:
            accordion_default_open = "upload-proofs"
        else:
            accordion_default_open = "change-properties"

    if request.user.production_user == productionstream.officer:
        if not productionstream.work_logs.all():
            accordion_default_open = "work-log"
        elif not productionstream.proofs.all():
            accordion_default_open = "upload-proofs"

    if productionstream.status == constants.PRODUCTION_STREAM_INITIATED:
        accordion_default_open = "change-properties"

    context = {
        "productionstream": productionstream,
        "accordion_default_open": accordion_default_open,
    }
    return render(
        request,
        "production/_hx_productionstream_details_contents.html",
        context,
    )


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def _hx_productionstream_actions_change_properties(request, productionstream_id):
    productionstream = get_object_or_404(ProductionStream, pk=productionstream_id)

    status_form = StreamStatusForm(
        instance=productionstream,
        production_user=request.user.production_user,
        auto_id=f"productionstream_{productionstream.id}_id_%s",
    )
    supervisor_form = AssignSupervisorForm(
        instance=productionstream,
        auto_id=f"productionstream_{productionstream.id}_id_%s",
    )
    invitations_officer_form = AssignInvitationsOfficerForm(
        instance=productionstream,
        auto_id=f"productionstream_{productionstream.id}_id_%s",
    )
    officer_form = AssignOfficerForm(
        instance=productionstream,
        auto_id=f"productionstream_{productionstream.id}_id_%s",
    )

    context = {
        "productionstream": productionstream,
        "status_form": status_form,
        "supervisor_form": supervisor_form,
        "officer_form": officer_form,
        "invitations_officer_form": invitations_officer_form,
    }
    return render(
        request,
        "production/_hx_productionstream_actions_change_properties.html",
        context,
    )


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def _hx_event_form(request, productionstream_id, event_id=None):
    """
    Create or update a ProductionEvent.
    """
    productionstream = get_object_or_404(ProductionStream, pk=productionstream_id)
    if event_id:
        productionevent = get_object_or_404(ProductionEvent, pk=event_id)
    else:
        productionevent = None
    if request.method == "POST":
        form = ProductionEventForm(request.POST, instance=productionevent)
        if form.is_valid():
            form.save()
            return redirect(
                reverse(
                    "production:_hx_productionstream_details_contents",
                    kwargs={
                        "productionstream_id": productionstream.id,
                    },
                )
            )
    elif productionevent:
        form = ProductionEventForm(instance=productionevent)
    else:
        form = ProductionEventForm(
            initial={
                "stream": productionstream,
                "noted_by": request.user.production_user,
            },
        )
    context = {
        "productionstream": productionstream,
        "productionevent_form": form,
    }
    return render(request, "production/_hx_productionstream_event_form.html", context)


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def _hx_event_delete(request, productionstream_id, event_id):
    productionstream = get_object_or_404(ProductionStream, pk=productionstream_id)
    ProductionEvent.objects.filter(pk=event_id).delete()
    return redirect(
        reverse(
            "production:_hx_productionstream_details_contents",
            kwargs={
                "productionstream_id": productionstream.id,
            },
        )
    )


################################
# 2023-05 HTMX refactoring end
################################


######################
# Production process #  2023-05  ALL BELOW TO BE REFACTORED to htmx-driven views
######################


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def production_old(request, stream_id=None):
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
            context["prodevent_form"] = ProductionEventForm_deprec()

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
    return render(request, "production/production_old.html", context)


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
    productionstream = get_object_or_404(streams, id=stream_id)
    prodevent_form = ProductionEventForm_deprec()
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
        instance=productionstream,
        production_user=request.user.production_user,
        auto_id=f"productionstream_{productionstream.id}_id_%s",
    )

    context = {
        "stream": productionstream,
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
    return redirect(reverse("production:production_old"))


@is_production_user()
@permission_required("scipost.can_promote_user_to_production_officer")
def _hx_team_promote_user(request):
    form = UserToOfficerForm(request.POST or None)
    if form.is_valid():
        if (officer := form.save()) and (user := getattr(officer, "user", None)):
            # Add permission group
            group = Group.objects.get(name="Production Officers")
            user.groups.add(group)
            messages.success(
                request, "{user} promoted to Production Officer".format(user=officer)
            )

    return render(
        request,
        "production/_hx_team_promote_user.html",
        {"form": form},
    )


@is_production_user()
@permission_required("scipost.can_view_production", raise_exception=True)
def add_event(request, stream_id):
    qs = ProductionStream.objects.ongoing()
    if not request.user.has_perm("scipost.can_assign_production_officer"):
        qs = qs.filter_for_user(request.user.production_user)

    stream = get_object_or_404(qs, pk=stream_id)
    prodevent_form = ProductionEventForm_deprec(request.POST or None)
    if prodevent_form.is_valid():
        prodevent = prodevent_form.save(commit=False)
        prodevent.stream = stream
        prodevent.noted_by = request.user.production_user
        prodevent.save()
        messages.success(request, "Comment added to Stream.")
    else:
        messages.warning(request, "The form was invalidly filled.")
    return redirect(reverse("production:production_old", args=(stream.id,)))


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
@permission_required_htmx(
    ("scipost.can_view_production",),
    message="You cannot view production.",
)
def _hx_productionstream_actions_work_log(request, productionstream_id):
    productionstream = get_object_or_404(ProductionStream, pk=productionstream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", productionstream):
        return HTMXPermissionsDenied("You cannot work in this stream.")

    if request.user.has_perm("scipost.can_view_all_production_streams"):
        types = constants.PRODUCTION_ALL_WORK_LOG_TYPES
    else:
        types = constants.PRODUCTION_OFFICERS_WORK_LOG_TYPES
    work_log_form = WorkLogForm(request.POST or None, log_types=types)

    if work_log_form.is_valid():
        log = work_log_form.save(commit=False)
        log.content = productionstream
        log.user = request.user
        log.save()
        messages.success(request, "Work Log added to Stream.")

    context = {
        "productionstream": productionstream,
        "work_log_form": work_log_form,
    }

    return render(
        request,
        "production/_hx_productionstream_actions_work_log.html",
        context,
    )


is_production_user()


@permission_required(
    "scipost.can_take_decisions_related_to_proofs", raise_exception=True
)
def update_status(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", stream):
        return redirect(reverse("production:production_old", args=(stream.id,)))

    p = request.user.production_user
    form = StreamStatusForm(request.POST or None, instance=stream, production_user=p)

    if form.is_valid():
        stream = form.save()
        messages.warning(request, "Production Stream succesfully changed status.")
    else:
        messages.warning(request, "The status change was invalid.")
    return redirect(stream.get_absolute_url())


@is_production_user()
@permission_required_htmx(
    (
        "scipost.can_view_production",
        "scipost.can_take_decisions_related_to_proofs",
    ),
    message="You do not have permission to update the status of this stream.",
    css_class="row",
)
def _hx_update_status(request, stream_id):
    productionstream = get_object_or_404(
        ProductionStream.objects.ongoing(), pk=stream_id
    )

    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", productionstream):
        return HTMXPermissionsDenied(
            "You cannot perform supervisory actions in this stream."
        )

    status_form = StreamStatusForm(
        request.POST or None,
        instance=productionstream,
        production_user=request.user.production_user,
        auto_id=f"productionstream_{productionstream.id}_id_%s",
    )

    if status_form.is_valid():
        status_form.save()
        status_form.fields["status"].choices = status_form.get_available_statuses()
        messages.success(request, "Production Stream succesfully changed status.")

    else:
        messages.error(request, "\\n".join(status_form.errors.values()))

    context = {
        "stream": productionstream,
        "form": status_form,
    }

    return render(
        request,
        "production/_hx_productionstream_change_status.html",
        context,
    )


@is_production_user()
@permission_required("scipost.can_assign_production_officer", raise_exception=True)
@transaction.atomic
def add_officer(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", stream):
        return redirect(reverse("production:production_old", args=(stream.id,)))

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
    return redirect(reverse("production:production_old", args=(stream.id,)))


@is_production_user()
@permission_required("scipost.can_assign_production_officer", raise_exception=True)
@transaction.atomic
def remove_officer(request, stream_id, officer_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", stream):
        return redirect(reverse("production:production_old", args=(stream.id,)))

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

    return redirect(reverse("production:production_old", args=(stream.id,)))


@is_production_user()
@permission_required_htmx(
    (
        "scipost.can_view_production",
        "scipost.can_assign_production_officer",
    ),
    message="You do not have permission to update the officer of this stream.",
    css_class="row",
)
@transaction.atomic
def _hx_update_officer(request, stream_id):
    productionstream = get_object_or_404(
        ProductionStream.objects.ongoing(), pk=stream_id
    )
    prev_officer = productionstream.officer

    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", productionstream):
        return HTMXPermissionsDenied(
            "You cannot perform supervisory actions in this stream."
        )

    officer_form = AssignOfficerForm(
        request.POST or None,
        instance=productionstream,
        auto_id=f"productionstream_{productionstream.id}_id_%s",
    )

    if officer_form.is_valid():
        officer_form.save()
        officer = officer_form.cleaned_data.get("officer")

        # Add officer to stream if they exist.
        if officer is not None:
            assign_perm("can_work_for_stream", officer.user, productionstream)
            messages.success(request, f"Officer {officer} has been assigned.")

            event = ProductionEvent(
                stream=productionstream,
                event="assignment",
                comments=" tasked Production Officer with proofs production:",
                noted_to=officer,
                noted_by=request.user.production_user,
            )
            event.save()

            # Temp fix.
            # TODO: Implement proper email
            ProductionUtils.load({"request": request, "stream": productionstream})
            ProductionUtils.email_assigned_production_officer()

        # Remove old officer.
        else:
            remove_perm("can_work_for_stream", prev_officer.user, productionstream)
            messages.success(request, f"Officer {prev_officer} has been removed.")

    else:
        messages.error(request, "\\n".join(officer_form.errors.values()))

    context = {
        "stream": productionstream,
        "form": officer_form,
    }

    return render(
        request,
        "production/_hx_productionstream_change_officer.html",
        context,
    )


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
    return redirect(reverse("production:production_old"))


@is_production_user()
@permission_required("scipost.can_promote_user_to_production_officer")
def _hx_team_delete_officer(request, officer_id):
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

    return HTMXResponse(
        "Production Officer {user} has been removed.".format(user=production_user),
        tag="danger",
    )


@is_production_user()
@permission_required("scipost.can_assign_production_officer", raise_exception=True)
@transaction.atomic
def add_invitations_officer(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", stream):
        return redirect(reverse("production:production_old", args=(stream.id,)))

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
    return redirect(reverse("production:production_old", args=(stream.id,)))


@is_production_user()
@permission_required("scipost.can_assign_production_officer", raise_exception=True)
@transaction.atomic
def remove_invitations_officer(request, stream_id, officer_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_perform_supervisory_actions", stream):
        return redirect(reverse("production:production_old", args=(stream.id,)))

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

    return redirect(reverse("production:production_old", args=(stream.id,)))


@is_production_user()
@permission_required_htmx(
    (
        "scipost.can_view_production",
        "scipost.can_assign_production_officer",
    ),
    message="You do not have permission to update the invitations officer of this stream.",
    css_class="row",
)
@transaction.atomic
def _hx_update_invitations_officer(request, stream_id):
    productionstream = get_object_or_404(
        ProductionStream.objects.ongoing(), pk=stream_id
    )
    prev_inv_officer = productionstream.invitations_officer
    checker = ObjectPermissionChecker(request.user)

    if not checker.has_perm("can_perform_supervisory_actions", productionstream):
        return HTMXPermissionsDenied(
            "You cannot perform supervisory actions in this stream."
        )

    invitations_officer_form = AssignInvitationsOfficerForm(
        request.POST or None,
        instance=productionstream,
        auto_id=f"productionstream_{productionstream.id}_id_%s",
    )
    if invitations_officer_form.is_valid():
        invitations_officer_form.save()
        inv_officer = invitations_officer_form.cleaned_data.get("invitations_officer")

        # Add invitations officer to stream if they exist.
        if inv_officer is not None:
            assign_perm("can_work_for_stream", inv_officer.user, productionstream)
            messages.success(
                request, f"Invitations Officer {inv_officer} has been assigned."
            )

            event = ProductionEvent(
                stream=productionstream,
                event="assignment",
                comments=" tasked Invitations Officer with invitations:",
                noted_to=inv_officer,
                noted_by=request.user.production_user,
            )
            event.save()

            # Temp fix.
            # TODO: Implement proper email
            ProductionUtils.load({"request": request, "stream": productionstream})
            ProductionUtils.email_assigned_invitation_officer()

        # Remove old invitations officer.
        else:
            remove_perm("can_work_for_stream", prev_inv_officer.user, productionstream)
            messages.success(
                request, f"Invitations Officer {prev_inv_officer} has been removed."
            )
    else:
        messages.error(request, "\\n".join(invitations_officer_form.errors.values()))

    context = {
        "stream": productionstream,
        "form": invitations_officer_form,
    }

    return render(
        request,
        "production/_hx_productionstream_change_invitations_officer.html",
        context,
    )


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
    return redirect(reverse("production:production_old", args=(stream.id,)))


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

    return redirect(reverse("production:production_old", args=(stream.id,)))


@method_decorator(is_production_user(), name="dispatch")
@method_decorator(
    permission_required("scipost.can_view_production", raise_exception=True),
    name="dispatch",
)
class UpdateEventView(UpdateView):
    model = ProductionEvent
    form_class = ProductionEventForm_deprec
    slug_field = "id"
    slug_url_kwarg = "event_id"

    def get_queryset(self):
        return self.model.objects.get_my_events(self.request.user.production_user)

    def form_valid(self, form):
        messages.success(self.request, "Event updated succesfully")
        return super().form_valid(form)


@is_production_user()
@permission_required_htmx(
    ("scipost.can_view_production", "scipost.can_assign_production_supervisor"),
    message="You do not have permission to update the supervisor of this stream.",
    css_class="row",
)
@transaction.atomic
def _hx_update_supervisor(request, stream_id):
    productionstream = get_object_or_404(
        ProductionStream.objects.ongoing(), pk=stream_id
    )
    supervisor_form = AssignSupervisorForm(
        request.POST or None,
        instance=productionstream,
        auto_id=f"productionstream_{productionstream.id}_id_%s",
    )
    prev_supervisor = productionstream.supervisor

    if supervisor_form.is_valid():
        supervisor_form.save()
        supervisor = supervisor_form.cleaned_data.get("supervisor")

        # Add supervisor to stream if they exist.
        if supervisor is not None:
            messages.success(request, f"Supervisor {supervisor} has been assigned.")

            assign_perm("can_work_for_stream", supervisor.user, productionstream)
            assign_perm(
                "can_perform_supervisory_actions", supervisor.user, productionstream
            )

            event = ProductionEvent(
                stream=productionstream,
                event="assignment",
                comments=" assigned Production Supervisor:",
                noted_to=supervisor,
                noted_by=request.user.production_user,
            )
            event.save()

            # Temp fix.
            # TODO: Implement proper email
            ProductionUtils.load({"request": request, "stream": productionstream})
            ProductionUtils.email_assigned_supervisor()

        # Remove old supervisor.
        else:
            remove_perm("can_work_for_stream", prev_supervisor.user, productionstream)
            remove_perm(
                "can_perform_supervisory_actions",
                prev_supervisor.user,
                productionstream,
            )
            messages.success(request, f"Supervisor {prev_supervisor} has been removed.")

    else:
        messages.error(request, "\\n".join(supervisor_form.errors.values()))

    context = {
        "stream": productionstream,
        "form": supervisor_form,
    }

    return render(
        request,
        "production/_hx_productionstream_change_supervisor.html",
        context,
    )


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
def _hx_mark_as_completed(request, stream_id):
    productionstream = get_object_or_404(
        ProductionStream.objects.ongoing(), pk=stream_id
    )
    productionstream.status = constants.PRODUCTION_STREAM_COMPLETED
    productionstream.closed = timezone.now()
    productionstream.save()

    production_event = ProductionEvent(
        stream=productionstream,
        event="status",
        comments=" marked the Production Stream as completed.",
        noted_by=request.user.production_user,
    )
    production_event.save()

    messages.success(
        request,
        "Production Stream has been marked as completed.",
    )

    return HttpResponse(
        r"""<summary class="text-white bg-success p-3">
                Production Stream has been marked as completed.
            </summary>"""
    )


@is_production_user()
@permission_required("scipost.can_assign_production_officer", raise_exception=True)
@transaction.atomic
def _hx_toggle_on_hold(request, stream_id):
    productionstream = get_object_or_404(
        ProductionStream.objects.ongoing(), pk=stream_id
    )

    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", productionstream):
        return HTMXPermissionsDenied("You cannot work in this stream.")

    productionstream.on_hold = not productionstream.on_hold
    productionstream.save()

    if productionstream.on_hold:
        production_event = ProductionEvent(
            stream=productionstream,
            event="status",
            comments=" marked the Production Stream as on hold.",
            noted_by=request.user.production_user,
        )
        messages.success(
            request,
            "Production Stream has been marked as on hold.",
        )
    else:
        production_event = ProductionEvent(
            stream=productionstream,
            event="status",
            comments=" unmarked the Production Stream as on hold.",
            noted_by=request.user.production_user,
        )
        messages.success(
            request,
            "Production Stream has been unmarked as on hold.",
        )

    production_event.save()

    return render(
        request,
        "production/_hx_productionstream_details.html",
        {"productionstream": productionstream},
    )


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
    return redirect(reverse("production:production_old"))


@is_production_user()
@permission_required_htmx(
    (
        "scipost.can_view_production",
        "scipost.can_upload_proofs",
    ),
    message="You cannot upload proofs for this stream.",
)
@transaction.atomic
def _hx_upload_proofs(request, stream_id):
    """
    Called by a member of the Production Team.
    Upload the production version .pdf of a submission.
    """
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)

    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", stream):
        return HTMXPermissionsDenied("You cannot work in this stream.")

    form = ProofsUploadForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        proofs = form.save(commit=False)
        proofs.stream = stream
        proofs.uploaded_by = request.user.production_user
        proofs.save()
        Proofs.objects.filter(stream=stream).exclude(version=proofs.version).exclude(
            status=constants.PROOFS_ACCEPTED
        ).update(status=constants.PROOFS_RENEWED)

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

    context = {"stream": stream, "form": form, "total_proofs": stream.proofs.count()}
    return render(request, "production/_hx_upload_proofs.html", context)


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
        return redirect(reverse("production:production_old"))

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
        return redirect(reverse("production:production_old"))

    try:
        proofs = stream.proofs.get(version=version)
    except Proofs.DoesNotExist:
        raise Http404

    context = {"stream": stream, "proofs": proofs}
    return render(request, "production/proofs.html", context)


@permission_required("scipost.can_view_production", raise_exception=True)
def proofs_pdf(request, slug):
    """Open Proofs pdf."""
    if not request.user.is_authenticated:
        # Don't use the decorator but this strategy,
        # because now it will return 404 instead of a redirect to the login page.
        raise Http404

    proofs = get_object_or_404(Proofs, id=proofs_slug_to_id(slug))
    stream = proofs.stream

    # Check if user has access!η
    checker = ObjectPermissionChecker(request.user)
    can_work_for_stream = checker.has_perm("can_work_for_stream", stream)
    is_submission_author = request.user.contributor in stream.submission.authors.all()

    if not (can_work_for_stream or is_submission_author):
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
        return redirect(reverse("production:production_old"))

    try:
        proofs = stream.proofs.exclude(status=constants.PROOFS_UPLOADED).get(
            version=version
        )
    except Proofs.DoesNotExist:
        raise Http404

    proofs.accessible_for_authors = not proofs.accessible_for_authors
    proofs.save()
    messages.success(request, "Proofs accessibility updated.")
    return redirect(reverse("production:proofs", args=(stream.id, proofs.version)))


@is_production_user()
@permission_required_htmx(
    (
        "scipost.can_view_production",
        "scipost.can_take_decisions_related_to_proofs",
        "scipost.can_run_proofs_by_authors",
    ),
    message="You cannot make proofs accessible to the authors.",
)
def _hx_toggle_accessibility(request, stream_id, version):
    """
    Open/close accessibility of proofs to the authors.
    """
    stream = get_object_or_404(ProductionStream.objects.all(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", stream):
        return HTMXPermissionsDenied("You cannot work in this stream.")

    try:
        proofs = stream.proofs.exclude(status=constants.PROOFS_UPLOADED).get(
            version=version
        )
    except Proofs.DoesNotExist:
        return HTMXResponse("Proofs do not exist.", tag="danger")

    proofs.accessible_for_authors = not proofs.accessible_for_authors
    proofs.save()
    messages.success(request, "Proofs accessibility updated.")
    return render(
        request,
        "production/_hx_productionstream_actions_proofs_item.html",
        {
            "stream": stream,
            "proofs": proofs,
            "total_proofs": stream.proofs.count(),
            "active_id": proofs.version,
        },
    )


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
        return redirect(reverse("production:production_old"))

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
@permission_required_htmx(
    (
        "scipost.can_view_production",
        "scipost.can_take_decisions_related_to_proofs",
        "scipost.can_run_proofs_by_authors",
    ),
    message="You cannot accept or decline proofs.",
)
@transaction.atomic
def _hx_proofs_decision(request, stream_id, version, decision):
    """
    Send/open proofs to the authors. This decision is taken by the supervisor.
    """
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", stream):
        return HTMXPermissionsDenied("You cannot work in this stream.")

    try:
        proofs = stream.proofs.get(version=version, status=constants.PROOFS_UPLOADED)
    except Proofs.DoesNotExist:
        return HTMXResponse("Proofs do not exist.", tag="danger")

    if decision == "accept":
        stream.status = constants.PROOFS_CHECKED
        proofs.status = constants.PROOFS_ACCEPTED_SUP
        decision = "accepted"
    else:
        stream.status = constants.PROOFS_TASKED
        proofs.status = constants.PROOFS_DECLINED_SUP
        proofs.accessible_for_authors = False
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
    messages.success(request, f"Proofs have been {decision}.")
    return render(
        request,
        "production/_hx_productionstream_actions_proofs_item.html",
        {
            "stream": stream,
            "proofs": proofs,
            "total_proofs": stream.proofs.count(),
            "active_id": proofs.version,
        },
    )


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
        return redirect(reverse("production:production_old"))

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

    mail_request = MailEditorSubviewHTMX(
        request, "production_send_proofs", proofs=proofs
    )
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


@is_production_user()
@permission_required_htmx(
    (
        "scipost.can_view_production",
        "scipost.can_take_decisions_related_to_proofs",
        "scipost.can_run_proofs_by_authors",
    ),
    message="You cannot send proofs to the authors.",
)
@transaction.atomic
def _hx_send_proofs(request, stream_id, version):
    """
    Send/open proofs to the authors.
    """
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm("can_work_for_stream", stream):
        return HTMXPermissionsDenied("You cannot work in this stream.")

    try:
        proofs = stream.proofs.can_be_send().get(version=version)
    except Proofs.DoesNotExist:
        return HTMXResponse("Proofs do not exist.", tag="danger")

    proofs.status = constants.PROOFS_SENT
    proofs.accessible_for_authors = True

    if stream.status not in [
        constants.PROOFS_PUBLISHED,
        constants.PROOFS_CITED,
        constants.PRODUCTION_STREAM_COMPLETED,
    ]:
        stream.status = constants.PROOFS_SENT
        stream.save()

    mail_request = MailEditorSubviewHTMX(
        request,
        "production_send_proofs",
        proofs=proofs,
        context={
            "view_url": reverse("production:_hx_send_proofs", args=[stream_id, version])
        },
    )

    print(request)

    if request.method == "GET":
        return mail_request.interrupt()

    if mail_request.is_valid():
        proofs.save()
        stream.save()

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

        messages.success(request, "Proofs have been sent.")
        return HTMXResponse("Proofs have been sent to the authors.", tag="success")
    else:
        messages.error(request, "Proofs have not been sent.")
        return HTMXResponse(
            "Proofs have not been sent. Please check the form.", tag="danger"
        )


def _hx_productionstream_change_action_buttons(request, productionstream_id, key):
    productionstream = get_object_or_404(ProductionStream, pk=productionstream_id)

    # Get either the id, or the id of the object and convert it to a string
    # If this fails, set to "None"
    current_option = getattr(productionstream, key, None)
    current_option = getattr(current_option, "id", current_option)
    current_option_str = str(current_option)

    # Get the new option from the POST request, which is a string
    # Set to "None" if the string is empty
    new_option = request.POST.get(key, None)
    new_option_str = str(new_option) or "None"

    return render(
        request,
        "production/_hx_productionstream_change_action_buttons.html",
        {
            "current_option": current_option_str,
            "new_option": new_option_str,
        },
    )


def _hx_productionstream_summary_assignees_status(request, productionstream_id):
    productionstream = get_object_or_404(ProductionStream, pk=productionstream_id)

    context = {
        "productionstream": productionstream,
    }

    return render(
        request,
        "production/_hx_productionstream_summary_assignees_status.html",
        context,
    )


def _hx_productionstream_search_form(request, filter_set: str):
    productionstream_search_form = ProductionStreamSearchForm(
        user=request.user,
        session_key=request.session.session_key,
    )

    if filter_set == "empty":
        productionstream_search_form.apply_filter_set({}, none_on_empty=True)
    # TODO: add more filter sets saved in the session of the user

    context = {
        "form": productionstream_search_form,
    }
    return render(request, "production/_hx_productionstream_search_form.html", context)


def _hx_event_list(request, productionstream_id):
    productionstream = get_object_or_404(ProductionStream, pk=productionstream_id)

    context = {
        "productionstream": productionstream,
        "events": productionstream.events.all_without_duration,
    }

    return render(
        request,
        "production/_productionstream_events.html",
        context,
    )


def _hx_productionstream_actions_bulk_assign_officers(request):
    if request.POST:
        productionstream_ids = (
            request.POST.getlist("productionstream-bulk-action-selected") or []
        )
        productionstreams = ProductionStream.objects.filter(pk__in=productionstream_ids)

        form = BulkAssignOfficersForm(
            request.POST,
            productionstreams=productionstreams,
            auto_id="productionstreams-bulk-action-form-%s",
        )

    else:
        form = BulkAssignOfficersForm()

    # Render the form if it is not valid (usually when post data is missing)
    if not form.is_valid():
        return render(
            request,
            "production/_hx_productionstream_actions_bulk_assign_officer.html",
            {"form": form},
        )

    if officer := form.cleaned_data["officer"]:
        if not request.user.has_perm("scipost.can_assign_production_officer"):
            messages.error(
                request, "You do not have permission to assign officers to streams."
            )
        else:
            # Create events, update permissions, send emails for each stream
            for productionstream in form.productionstreams:
                old_officer = productionstream.officer

                if old_officer == officer:
                    continue

                if productionstream.status in [
                    constants.PRODUCTION_STREAM_INITIATED,
                    constants.PROOFS_SOURCE_REQUESTED,
                ]:
                    productionstream.status = constants.PROOFS_TASKED

                productionstream.officer = officer
                productionstream.save()

                event = ProductionEvent(
                    stream=productionstream,
                    event="assignment",
                    comments=" tasked Production Officer with proofs production:",
                    noted_to=officer,
                    noted_by=request.user.production_user,
                )
                event.save()

                # Update permissions
                assign_perm("can_work_for_stream", officer.user, productionstream)
                if old_officer is not None:
                    remove_perm(
                        "can_work_for_stream", old_officer.user, productionstream
                    )

            # Temp fix.
            # TODO: Implement proper email
            ProductionUtils.load(
                {
                    "request": request,
                    "officer": officer,
                    "streams": form.productionstreams,
                }
            )
            ProductionUtils.email_assigned_production_officer_bulk()

            messages.success(
                request,
                f"Assigned {officer} as production officer to the selected streams.",
            )

    if (supervisor := form.cleaned_data["supervisor"]) and not request.user.has_perm(
        "scipost.can_assign_production_supervisor"
    ):
        messages.error(
            request, "You do not have permission to assign supervisors to streams."
        )
    elif supervisor is not None:
        for productionstream in form.productionstreams:
            old_supervisor = productionstream.supervisor

            if old_supervisor == supervisor:
                continue

            productionstream.supervisor = supervisor
            productionstream.save()

            event = ProductionEvent(
                stream=productionstream,
                event="assignment",
                comments=" assigned Production Supervisor:",
                noted_to=supervisor,
                noted_by=request.user.production_user,
            )
            event.save()

            # Update permissions
            assign_perm("can_work_for_stream", supervisor.user, productionstream)
            assign_perm(
                "can_perform_supervisory_actions",
                supervisor.user,
                productionstream,
            )
            if old_supervisor is not None:
                remove_perm(
                    "can_work_for_stream", old_supervisor.user, productionstream
                )
                remove_perm(
                    "can_perform_supervisory_actions",
                    old_supervisor.user,
                    productionstream,
                )

        # Temp fix.
        # TODO: Implement proper email
        ProductionUtils.load(
            {
                "request": request,
                "supervisor": supervisor,
                "streams": form.productionstreams,
            }
        )
        ProductionUtils.email_assigned_supervisor_bulk()

        messages.success(
            request,
            f"Assigned {supervisor} as supervisor to the selected streams.",
        )

    return render(
        request,
        "production/_hx_productionstream_actions_bulk_assign_officer.html",
        {"form": form},
    )


@permission_required(
    "scipost.can_promote_user_to_production_officer", raise_exception=True
)
def production_team(request):
    context = {
        "production_officers": ProductionUser.objects.active().filter(
            user__groups__name="Production Officers"
        ),
        "new_officer_form": UserToOfficerForm(),
    }
    return render(request, "production/production_team.html", context)


@permission_required(
    "scipost.can_promote_user_to_production_officer", raise_exception=True
)
def production_team_list(request):
    context = {
        "officers": ProductionUser.objects.active().filter(
            user__groups__name="Production Officers"
        ),
    }
    return render(request, "production/production_team_list.html", context)
