__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView

from colleges.models import Fellowship
from colleges.forms import FellowshipSelectForm, FellowshipDynSelForm
from scipost.mixins import PermissionsMixin

from .forms import ProceedingsForm
from .models import Proceedings


@login_required
@permission_required("scipost.can_draft_publication", raise_exception=True)
def proceedings(request):
    """
    List all Proceedings
    """
    context = {"proceedings": Proceedings.objects.all()}
    return render(request, "proceedings/proceedings.html", context)


@login_required
@permission_required("scipost.can_draft_publication", raise_exception=True)
def proceedings_details(request, id):
    """
    Show Proceedings details
    """
    proceedings = get_object_or_404(Proceedings, id=id)
    context = {
        "proceedings": proceedings,
    }
    return render(request, "proceedings/proceedings_details.html", context)


class ProceedingsAddView(PermissionsMixin, CreateView):
    models = Proceedings
    form_class = ProceedingsForm
    permission_required = "scipost.can_draft_publication"
    template_name = "proceedings/proceedings_add.html"


class ProceedingsUpdateView(PermissionsMixin, UpdateView):
    models = Proceedings
    form_class = ProceedingsForm
    permission_required = "scipost.can_draft_publication"
    template_name = "proceedings/proceedings_edit.html"

    def get_object(self):
        return get_object_or_404(Proceedings, id=self.kwargs["id"])


@permission_required("scipost.can_draft_publication")
def _hx_proceedings_fellowships(request, id):
    proceedings = get_object_or_404(Proceedings, pk=id)
    form = FellowshipDynSelForm(
        initial={
            "action_url_name": "proceedings:_hx_proceedings_fellowship_action",
            "action_url_base_kwargs": {"id": proceedings.id, "action": "add"},
            "action_target_element_id": "fellowships",
        }
    )
    context = {"proceedings": proceedings, "fellowship_search_form": form}
    return render(request, "proceedings/_hx_proceedings_fellowships.html", context)


@permission_required("scipost.can_draft_publication")
def _hx_proceedings_fellowship_action(request, id, fellowship_id, action):
    proceedings = get_object_or_404(Proceedings, pk=id)
    fellowship = get_object_or_404(Fellowship, pk=fellowship_id)
    if action == "add":
        proceedings.fellowships.add(fellowship)
        # Also add to all existing Submissions
        for submission in proceedings.submissions.all():
            submission.fellows.add(fellowship)
    if action == "remove":
        # If this Fellow is EiC of any submission, abort
        if proceedings.submissions.filter(
            editor_in_charge=fellowship.contributor
        ).exists():
            messages.error(
                request,
                f"Fellow {fellowship.contributor} is EiC for some Submissions; removal aborted.",
            )
        else:
            proceedings.fellowships.remove(fellowship)
            for submission in proceedings.submissions.all():
                submission.fellows.remove(fellowship)
    return redirect(
        reverse(
            "proceedings:_hx_proceedings_fellowships", kwargs={"id": proceedings.id}
        )
    )
