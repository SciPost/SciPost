__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.views.generic import UpdateView
from django.views.generic.list import ListView
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404

from invitations.models import RegistrationInvitation

from .forms import MailchimpUpdateForm
from .models import MailchimpList


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

    template_name = "mailing_lists/overview.html"
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
    return redirect(reverse("mailing_lists:overview"))


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
    unsubscribed, subscribed, response = form.sync_members(_list)

    # Let the user know
    text = "<h3>Syncronize members complete.</h3>"
    if unsubscribed:
        text += "<br>%i members have succesfully been unsubscribed." % unsubscribed
    if subscribed:
        text += "<br>%i members have succesfully been subscribed." % subscribed
    messages.success(request, text)
    return redirect(_list.get_absolute_url() + "?bulkid=" + response.get("id"))


class ListDetailView(MailchimpMixin, UpdateView):
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
