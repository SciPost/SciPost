__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from datetime import date
import re
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.datetime_safe import date

from colleges.forms import FellowshipsMonitorSearchForm
from colleges.models.fellowship import Fellowship
from scipost.permissions import permission_required_htmx


@login_required()
@permission_required("scipost.can_view_fellowships_monitor", raise_exception=True)
def fellowships_monitor(request):
    return render(request, "colleges/fellowships_monitor/fellowships_monitor.html")


@permission_required_htmx(
    "scipost.can_view_fellowships_monitor",
    "You do not have permission to view the fellowships monitor.",
)
def _hx_table(request):
    form = FellowshipsMonitorSearchForm(
        request.POST or None,
        user=request.user,
        session_key=request.session.session_key,
    )
    if form.is_valid():
        fellowships = form.search_results()
    else:
        fellowships = Fellowship.objects.all()
    paginator = Paginator(fellowships, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index
    context = {
        "count": count,
        "page_obj": page_obj,
        "start_index": start_index,
    }
    return render(request, "colleges/fellowships_monitor/_hx_table.html", context)


def _hx_search_form(request, filter_set: str):
    DATE_REGEX = r"\d{4}-\d{2}-\d{2}"
    form = FellowshipsMonitorSearchForm(
        user=request.user,
        session_key=request.session.session_key,
    )

    if filter_set == "empty":
        form.apply_filter_set(
            {
                "has_regular": True,
                "has_senior": True,
                "has_guest": True,
            },
            none_on_empty=True,
        )
    elif m := re.match(f"^from_({DATE_REGEX})_to_({DATE_REGEX})$", filter_set):
        date_from = date.fromisoformat(m.group(1))
        date_to = date.fromisoformat(m.group(2))
        form.apply_filter_set(
            {
                "date_from": date_from,
                "date_to": date_to,
            }
        )

    context = {
        "form": form,
    }
    return render(request, "colleges/fellowships_monitor/_hx_search_form.html", context)
