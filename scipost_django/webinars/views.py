__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Webinar
from .forms import WebinarRegistrationForm

from mails.utils import DirectMailUtil


def webinar_detail(request, slug):
    webinar = get_object_or_404(
        Webinar.objects.prefetch_related("participants"),
        slug=slug,
    )
    initial = {"webinar": webinar,}
    if request.user.is_authenticated:
        initial["first_name"] = request.user.first_name
        initial["last_name"] = request.user.last_name
        initial["email"] = request.user.email
        if request.user.contributor:
            initial[
                "organization"
            ] = request.user.contributor.profile.affiliations.current().first()
    form = WebinarRegistrationForm(initial=initial)
    context = {
        "webinar": webinar,
        "registration_form": form,
    }
    return render(request, "webinars/webinar_detail.html", context)


def webinar_register(request, slug):
    webinar = get_object_or_404(Webinar, slug=slug)
    form = WebinarRegistrationForm(request.POST or None)
    if form.is_valid():
        registration = form.save()
        mail_sender = DirectMailUtil(
            "webinars/webinar_registration_ack",
            delayed_processing=False,
            bcc=[
                "admin@{domain}".format(domain=Site.objects.get_current().domain),
            ],
            registration=registration,
        )
        mail_sender.send_mail()
        messages.success(
            request,
            ("Thank you for registering for this online webinar. "
            "We sent you a confirmation email.")
        )
    else:
        for error_messages in form.errors.values():
            messages.warning(request, *error_messages)
    return redirect(reverse("webinars:webinar_detail", kwargs={"slug": slug}))
