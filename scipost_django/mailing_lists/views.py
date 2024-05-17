__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.generic import UpdateView
from django.views.generic.list import ListView
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404

from invitations.models import RegistrationInvitation
from scipost.permissions import HTMXResponse

from .forms import (
    MailchimpUpdateForm,
    MailingListForm,
    NewsletterForm,
    NewsletterUploadMediaForm,
)
from .models import MailchimpList, MailingList, Newsletter


class MailchimpMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = "scipost.can_manage_mailchimp"
    raise_exception = True


class MailchimpListView(MailchimpMixin, ListView):
    """
    List all lists of Mailchimp known to the current database.
    This is part of the editorial actions for SciPost Administrators.
    It should act as a main page from which the admin can to action to update
    some general mailchimp settings.
    """

    template_name = "mailing_lists/mailchimp_overview.html"
    model = MailchimpList


@login_required
@permission_required("scipost.can_manage_mailchimp", raise_exception=True)
def syncronize_lists(request):
    """
    Syncronize the Mailchimp lists in the database with the lists known in
    the mailchimp account which is related to the API_KEY.
    """
    form = MailchimpUpdateForm()
    updated = form.sync()
    messages.success(
        request, "%i mailing lists have succesfully been updated." % updated
    )
    return redirect(reverse("mailing_lists:mailchimp_overview"))


@login_required
@permission_required(
    "scipost.can_read_all_privacy_sensitive_data", raise_exception=True
)
def export_non_registered_invitations(request):
    """
    Syncronize the Mailchimp lists in the database with the lists known in
    the mailchimp account which is related to the API_KEY.
    """
    invitations = RegistrationInvitation.objects.declined_or_without_response()

    response = HttpResponse(content_type="text/csv")
    filename = "export_{timestamp}_non_registered_invitations.csv".format(timestamp="")
    response["Content-Disposition"] = "attachment; filename={filename}".format(
        filename=filename
    )

    writer = csv.writer(response)
    writer.writerow(["Email address", "First Name", "Last Name"])
    for invitation in invitations:
        writer.writerow([invitation.email, invitation.first_name, invitation.last_name])
    return response


@login_required
@permission_required("scipost.can_manage_mailchimp", raise_exception=True)
def syncronize_members(request, list_id):
    """
    Syncronize the Mailchimp lists in the database with the lists known in
    the mailchimp account which is related to the API_KEY.
    """
    _list = get_object_or_404(MailchimpList, mailchimp_list_id=list_id)
    form = MailchimpUpdateForm()
    unsubscribed, subscribed, response = form.sync_mailchimp_members(_list)

    # Let the user know
    text = "<h3>Syncronize members complete.</h3>"
    if unsubscribed:
        text += "<br>%i members have succesfully been unsubscribed." % unsubscribed
    if subscribed:
        text += "<br>%i members have succesfully been subscribed." % subscribed
    messages.success(request, text)
    return redirect(_list.get_absolute_url() + "?bulkid=" + response.get("id"))


class MailchimpListDetailView(MailchimpMixin, UpdateView):
    """
    The detail view of a certain Mailchimp list. This allows the admin to i.e. manage group
    permissions to the group.
    """

    slug_field = "mailchimp_list_id"
    slug_url_kwarg = "list_id"
    fields = ("allowed_groups", "internal_name", "open_for_subscription")
    model = MailchimpList

    def form_valid(self, form):
        messages.success(self.request, "List succesfully updated")
        return super().form_valid(form)


def manage(request):
    """
    Manage mailing lists and newsletters
    """
    mailing_lists = MailingList.objects.all()
    newsletters = Newsletter.objects.all()
    return TemplateResponse(
        request,
        "mailing_lists/manage.html",
        {
            "mailing_lists": mailing_lists,
            "newsletters": newsletters,
        },
    )


def _hx_mailing_list_create(request):
    """
    Render the mailing list creation form and handle the response.
    """

    form = MailingListForm(request.POST or None)

    if form.is_valid():
        form.save()
        response = HTMXResponse("Mailing list created successfully", tag="success")
        response["HX-Trigger"] = "new-mailing-list-created"

        return response

    return TemplateResponse(
        request,
        "mailing_lists/_hx_mailing_list_form.html",
        {"form": form},
    )


def _hx_mailing_list_list(request):
    """
    List all mailing lists.
    """
    mailing_lists = MailingList.objects.all()
    return TemplateResponse(
        request,
        "mailing_lists/_hx_mailing_list_list.html",
        {"mailing_lists": mailing_lists},
    )


def _hx_newsletter_create(request, mailing_list_id):
    """
    Create a new newsletter under the given mailing list and return the new item.
    """
    mailing_list = get_object_or_404(MailingList, id=mailing_list_id)

    newsletter = Newsletter.objects.create(
        mailing_list=mailing_list, title="New newsletter"
    )

    return TemplateResponse(
        request,
        "mailing_lists/_hx_newsletter_list_item.html",
        {"newsletter": newsletter},
    )


def newsletter_edit(request, pk):
    """
    Load a newsletter and render the write template.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    return TemplateResponse(
        request,
        "mailing_lists/newsletter_write.html",
        {"newsletter": newsletter},
    )


def _hx_newsletter_form(request, pk):
    """
    Handle the submission of the newsletter form.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    form = NewsletterForm(request.POST or None, instance=newsletter)

    if form.is_valid():
        form.save()

    response = TemplateResponse(
        request,
        "mailing_lists/_hx_newsletter_form.html",
        {"form": form, "newsletter": newsletter},
    )

    response["HX-Trigger"] = "newsletter-updated"

    return response


def _hx_newsletter_display(request, pk):
    """
    Display the newsletter content.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    return TemplateResponse(
        request,
        "mailing_lists/_newsletter_email_body.html",
        {"newsletter": newsletter},
    )


def _hx_newsletter_send(request, pk):
    """
    Send the newsletter to all subscribers.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)
    try:
        newsletter.send()
        return HTMXResponse("Newsletter sent successfully", tag="success")
    except Exception as e:
        return HTMXResponse(f"Failed to send newsletter: {e}", tag="danger")


def _hx_toggle_subscription(request, pk):
    """
    Toggle the subscription status of a user to a certain list.
    Return the rerendered list item.
    """
    mailing_list = get_object_or_404(MailingList, pk=pk)
    is_subscribed = request.user.contributor in mailing_list.subscribed.all()

    print("Toggle subscription", is_subscribed, request.user.contributor, mailing_list)

    if is_subscribed:
        mailing_list.unsubscribe(request.user.contributor)
    else:
        mailing_list.subscribe(request.user.contributor)

    return TemplateResponse(
        request,
        "mailing_lists/_hx_mailing_list_item.html",
        {"mailing_list": mailing_list},
    )


def _hx_newsletter_media_form(request, pk):
    """
    Handle the addition of media to a newsletter.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    form = NewsletterUploadMediaForm(
        request.POST or None,
        request.FILES or None,
        newsletter=newsletter,
    )

    if form.is_valid():
        form.save()

    response = TemplateResponse(
        request,
        "mailing_lists/_hx_newsletter_media_form.html",
        {"form": form, "newsletter": newsletter},
    )

    if form.is_valid():
        response["HX-Trigger"] = "newsletter-media-updated"

    return response


def _hx_newsletter_media_embed(request, pk, media_pk):
    """
    Append the embed code for a media item to the newsletter, and rerender the form.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)
    try:
        media_item = newsletter.media[media_pk - 1]
    except IndexError:
        return HTMXResponse("Media item not found", tag="danger")

    img_tag = '<img src="{path}" alt="{name}" />'.format(
        path=media_item.get("path"), name=media_item.get("name")
    )
    newsletter.content += img_tag
    newsletter.save()

    return _hx_newsletter_form(request, pk)


def _hx_newsletter_media_embed_list(request, pk):
    """
    Return a list of all media items in the newsletter.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    return TemplateResponse(
        request,
        "mailing_lists/_hx_newsletter_media_embed_list.html",
        {"newsletter": newsletter},
    )
