from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import UpdateView
from django.views.generic.list import ListView
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from .forms import MailchimpUpdateForm
from .models import MailchimpList


class MailchimpMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = 'scipost.can_manage_mailchimp'
    raise_exception = True


class MailchimpListView(MailchimpMixin, ListView):
    """
    List all lists of Mailchimp known to the current database.
    This is part of the editorial actions for SciPost Administrators.
    It should act as a main page from which the admin can to action to update
    some general mailchimp settings.
    """
    template_name = 'mailing_lists/overview.html'
    model = MailchimpList


@login_required
@permission_required('scipost.can_manage_mailchimp', raise_exception=True)
def syncronize_lists(request):
    """
    Syncronize the Mailchimp lists in the database with the lists known in
    the mailchimp account which is related to the API_KEY.
    """
    form = MailchimpUpdateForm()
    updated = form.sync()
    messages.success(request, '%i mailing lists have succesfully been updated.' % updated)
    return redirect(reverse('mailing_lists:overview'))


class ListDetailView(MailchimpMixin, UpdateView):
    """
    The detail view of a certain Mailchimp list. This allows the admin to i.e. manage group
    permissions to the group.
    """
    slug_field = 'mailchimp_list_id'
    slug_url_kwarg = 'list_id'
    fields = ('allowed_groups', 'internal_name', 'supporting_text')
    model = MailchimpList

    def form_valid(self, form):
        messages.success(self.request, 'List succesfully updated')
        return super().form_valid(form)
