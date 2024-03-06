__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.urls import reverse

from colleges.permissions import fellowship_required
from submissions.forms.appraisal import RadioAppraisalForm
from submissions.models import Submission, Qualification, Readiness
from submissions.forms import QualificationForm, ReadinessForm


@fellowship_required()
def _hx_appraisal(request, identifier_w_vn_nr=None):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    context = {"submission": submission}
    fellowship = request.user.contributor.session_fellowship(request)
    return render(
        request,
        "submissions/pool/_hx_appraisal.html",
        context,
    )


@fellowship_required()
def _hx_qualification_form(request, identifier_w_vn_nr=None):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    fellow = request.user.contributor.session_fellowship(request)
    try:
        instance = Qualification.objects.get(submission=submission, fellow=fellow)
    except Qualification.DoesNotExist:
        instance = None
    if request.method == "POST":
        form = QualificationForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            response = render(
                request,
                "submissions/pool/_hx_appraisal.html",
                context={"submission": submission},
            )
            response["HX-Retarget"] = f"#submission-{submission.id}-appraisal"
            return response
    else:
        if instance:
            form = QualificationForm(instance=instance)
        else:
            form = QualificationForm(
                initial={"submission": submission, "fellow": fellow},
            )
    context = {
        "submission": submission,
        "form": form,
    }
    return render(
        request,
        "submissions/pool/_hx_qualification_form.html",
        context,
    )


@fellowship_required()
def _hx_readiness_form(request, identifier_w_vn_nr=None):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    fellow = request.user.contributor.session_fellowship(request)
    try:
        instance = Readiness.objects.get(submission=submission, fellow=fellow)
    except Readiness.DoesNotExist:
        instance = None
    if request.method == "POST":
        form = ReadinessForm(request.POST, instance=instance)
        if form.is_valid():
            if form.cleaned_data["choice"] == "yes":
                response = HttpResponse()
                response["HX-Redirect"] = reverse(
                    "submissions:pool:editorial_assignment",
                    kwargs={
                        "identifier_w_vn_nr": identifier_w_vn_nr,
                    },
                )
                return response
            form.save()
            response = render(
                request,
                "submissions/pool/_hx_appraisal.html",
                context={"submission": submission},
            )
            response["HX-Retarget"] = f"#submission-{submission.id}-appraisal"
            return response
    else:
        if instance:
            form = ReadinessForm(instance=instance)
        else:
            form = ReadinessForm(
                initial={"submission": submission, "fellow": fellow},
            )
    context = {
        "submission": submission,
        "form": form,
    }
    return render(
        request,
        "submissions/pool/_hx_readiness_form.html",
        context,
    )


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
