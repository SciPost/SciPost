__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse

from colleges.permissions import fellowship_required
from submissions.forms.appraisal import (
    ConditionalAssignmentOfferInlineForm,
    RadioAppraisalForm,
)
from submissions.models import Submission, Qualification, Readiness
from submissions.forms import QualificationForm, ReadinessForm


@fellowship_required()
def _hx_radio_appraisal_form(request, identifier_w_vn_nr=None):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    fellow = request.user.contributor.session_fellowship(request)

    try:
        qualification = Qualification.objects.get(submission=submission, fellow=fellow)
        readiness = Readiness.objects.get(submission=submission, fellow=fellow)
    except (Qualification.DoesNotExist, Readiness.DoesNotExist):
        qualification = readiness = None

    form = RadioAppraisalForm(
        request.POST or None,
        submission=submission,
        fellow=fellow,
        initial={
            "expertise_level": qualification.expertise_level if qualification else None,
            "readiness": readiness.status if readiness else None,
        },
    )

    if request.method == "POST":
        if form.is_valid():
            if form.should_redirect_to_editorial_assignment():
                response = HttpResponse()
                response["HX-Redirect"] = reverse(
                    "submissions:pool:editorial_assignment",
                    kwargs={
                        "identifier_w_vn_nr": identifier_w_vn_nr,
                    },
                )
                return response
            else:
                form.save()

    context = {
        "submission": submission,
        "fellow": fellow,
        "form": form,
    }
    return TemplateResponse(
        request,
        "submissions/pool/_hx_radio_appraisal_form.html",
        context,
    )


@fellowship_required()
def _hx_conditional_assignment_offer_form(request, identifier_w_vn_nr=None):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    fellow = request.user.contributor.session_fellowship(request)
    offer = submission.conditional_assignment_offers.filter(
        offered_by=fellow.contributor
    ).first()

    form = ConditionalAssignmentOfferInlineForm(
        request.POST or None,
        instance=offer,
        submission=submission,
        offered_by=fellow.contributor,
        readonly=request.method == "GET" and offer is not None,
    )

    if request.method == "POST" and request.POST.get("submit"):
        if form.is_valid():
            form.save()

            response = HttpResponse()
            response["HX-Trigger"] = "conditional-assignment-offer-made"

            return response

    context = {
        "submission": submission,
        "form": form,
        "offer": offer,
    }
    return TemplateResponse(
        request,
        "submissions/pool/_hx_conditional_assignment_offer_form.html",
        context,
    )
