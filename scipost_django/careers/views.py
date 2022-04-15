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
    form_class = JobOpeningForm
    success_url = reverse_lazy("careers:jobopenings")

    def test_func(self):
        return self.request.user.has_perm("careers.add_jobopening")


class JobOpeningUpdateView(UserPassesTestMixin, UpdateView):
    model = JobOpening
    form_class = JobOpeningForm
    success_url = reverse_lazy("careers:jobopenings")

    def test_func(self):
        return self.request.user.has_perm("careers.add_jobopening")


class JobOpeningListView(ListView):
    model = JobOpening

    def get_queryset(self):
        qs = JobOpening.objects.all()
        if not self.request.user.has_perm("careers.add_jobopening"):
            qs = qs.publicly_visible()
        return qs


class JobOpeningDetailView(DetailView):
    model = JobOpening

    def get_queryset(self):
        qs = JobOpening.objects.all()
        if not self.request.user.has_perm("careers.add_jobopening"):
            qs = qs.publicly_visible()
        return qs


class JobOpeningApplyView(CreateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = "careers/jobopening_apply.html"

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        initial.update(
            {
                "status": JobApplication.RECEIVED,
                "jobopening": get_object_or_404(
                    JobOpening, slug=self.kwargs.get("slug")
                ),
            }
        )
        return initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["jobopening"] = get_object_or_404(
            JobOpening, slug=self.kwargs.get("slug")
        )
        return context

    def form_valid(self, form):
        self.object = form.save()
        mail_sender = DirectMailUtil(
            "careers/jobapplication_ack",
            delayed_processing=False,
            bcc=[
                "admin@{domain}".format(domain=get_current_domain()),
            ],
            jobapplication=self.object,
        )
        mail_sender.send_mail()
        return redirect(self.get_success_url())


def jobapplication_verify(request, uuid):
    jobapp = get_object_or_404(JobApplication, uuid=uuid)
    jobapp.status = jobapp.VERIFIED
    jobapp.save()
    messages.success(request, "Your email has been verified successfully.")
    return redirect(jobapp.get_absolute_url())


class JobApplicationDetailView(DetailView):
    model = JobApplication

    def get_object(self, *args, **kwargs):
        return get_object_or_404(JobApplication, uuid=self.kwargs.get("uuid"))
