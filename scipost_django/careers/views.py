__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from common.utils import get_current_domain
from mails.utils import DirectMailUtil

from .models import JobOpening, JobApplication
from .forms import JobOpeningForm, JobApplicationForm


class JobOpeningCreateView(UserPassesTestMixin, CreateView):
    model = JobOpening
    template_name = "careers/job_opening_form.html"
    form_class = JobOpeningForm
    success_url = reverse_lazy("careers:job_openings")

    def test_func(self):
        return self.request.user.has_perm("scipost.can_manage_job_openings")


class JobOpeningUpdateView(UserPassesTestMixin, UpdateView):
    model = JobOpening
    form_class = JobOpeningForm
    success_url = reverse_lazy("careers:job_openings")

    def test_func(self):
        return self.request.user.has_perm("scipost.can_manage_job_openings")


class JobOpeningListView(ListView):
    model = JobOpening
    template_name = "careers/job_opening_list.html"

    def get_queryset(self):
        qs = JobOpening.objects.all()
        if not self.request.user.has_perm("scipost.can_manage_job_openings"):
            qs = qs.publicly_visible()
        return qs


class JobOpeningDetailView(DetailView):
    model = JobOpening
    template_name = "careers/job_opening_detail.html"
    context_object_name = "job_opening"

    def get_queryset(self):
        qs = JobOpening.objects.all()
        if not self.request.user.has_perm("scipost.can_manage_job_openings"):
            qs = qs.publicly_visible()
        return qs


class JobOpeningApplyView(CreateView):
    model = JobApplication
    form_class = JobApplicationForm
    context_object_name = "job_opening"
    template_name = "careers/job_opening_apply.html"

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        initial.update(
            {
                "status": JobApplication.RECEIVED,
                "job_opening": get_object_or_404(
                    JobOpening, slug=self.kwargs.get("slug")
                ),
            }
        )
        return initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["job_opening"] = get_object_or_404(
            JobOpening, slug=self.kwargs.get("slug")
        )
        return context

    def form_valid(self, form):
        self.object = form.save()
        mail_sender = DirectMailUtil(
            "careers/job_application_ack",
            delayed_processing=False,
            bcc=[
                "admin@{domain}".format(domain=get_current_domain()),
            ],
            job_application=self.object,
        )
        mail_sender.send_mail()
        return redirect(self.get_success_url())


def job_application_verify(request, uuid):
    job_app = get_object_or_404(JobApplication, uuid=uuid)
    job_app.status = job_app.VERIFIED
    job_app.save()
    messages.success(request, "Your email has been verified successfully.")
    return redirect(job_app.get_absolute_url())


class JobApplicationDetailView(DetailView):
    model = JobApplication
    context_object_name = "job_application"
    template_name = "careers/job_application_detail.html"

    def get_object(self, *args, **kwargs):
        return get_object_or_404(JobApplication, uuid=self.kwargs.get("uuid"))
