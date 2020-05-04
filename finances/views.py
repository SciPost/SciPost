__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from .forms import SubsidyForm, SubsidyAttachmentForm, LogsFilter
from .models import Subsidy, SubsidyAttachment, WorkLog
from .utils import slug_to_id

from journals.models import Journal
from organizations.models import Organization
from scipost.mixins import PermissionsMixin



def balance(request):
    pubyears = range(int(timezone.now().strftime('%Y')), 2015, -1)
    journals = Journal.objects.all()
    context = { 'pubyears': pubyears }
    context['data'] = {}
    for year in pubyears:
        context['data'][str(year)] = {}
        year_expenditures = 0
        for journal in journals:
            npub = journal.get_publications().filter(publication_date__year=year).count()
            expenditures = npub * journal.cost_per_publication(year)
            context['data'][str(year)][journal.doi_label] = {
                'npub': npub,
                'cost_per_pub': journal.cost_per_publication(year),
                'expenditures': expenditures,
            }
            year_expenditures += expenditures
        context['data'][str(year)]['expenditures'] = year_expenditures
    print(context)
    return render(request, 'finances/balance.html', context)


#############
# Subsidies #
#############

class SubsidyCreateView(PermissionsMixin, CreateView):
    """
    Create a new Subsidy.
    """
    permission_required = 'scipost.can_manage_subsidies'
    model = Subsidy
    form_class = SubsidyForm
    template_name = 'finances/subsidy_form.html'

    def get_success_url(self):
        return reverse_lazy('finances:subsidy_details', kwargs={'pk': self.object.id})


class SubsidyUpdateView(PermissionsMixin, UpdateView):
    """
    Update a Subsidy.
    """
    permission_required = 'scipost.can_manage_subsidies'
    model = Subsidy
    form_class = SubsidyForm
    template_name = 'finances/subsidy_form.html'

    def get_success_url(self):
        return reverse_lazy('finances:subsidy_details', kwargs={'pk': self.object.id})


class SubsidyDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a Subsidy.
    """
    permission_required = 'scipost.can_manage_subsidies'
    model = Subsidy
    success_url = reverse_lazy('finances:subsidies')


class SubsidyListView(ListView):
    model = Subsidy

    def get_queryset(self):
        qs = super().get_queryset()
        org = self.request.GET.get('org')
        if org:
            qs = qs.filter(organization__pk=org)
        order_by = self.request.GET.get('order_by')
        ordering = self.request.GET.get('ordering')
        if order_by == 'amount':
            qs = qs.filter(amount_publicly_shown=True).order_by('amount')
        elif order_by == 'date':
            qs = qs.order_by('date')
        elif order_by == 'until':
            qs = qs.order_by('date_until')
        if ordering == 'desc':
            qs = qs.reverse()
        return qs


class SubsidyDetailView(DetailView):
    model = Subsidy


def subsidy_toggle_amount_public_visibility(request, subsidy_id):
    """
    Method to toggle the public visibility of the amount of a Subsidy.
    Callable by Admin and Contacts for the relevant Organization.
    """
    subsidy = get_object_or_404(Subsidy, pk=subsidy_id)
    if not (request.user.has_perm('scipost.can_manage_subsidies') or
            request.user.has_perm('can_view_org_contacts', subsidy.organization)):
        raise PermissionDenied
    subsidy.amount_publicly_shown = not subsidy.amount_publicly_shown
    subsidy.save()
    messages.success(request, 'Amount visibility set to %s' % subsidy.amount_publicly_shown)
    return redirect(subsidy.get_absolute_url())


class SubsidyAttachmentCreateView(PermissionsMixin, CreateView):
    """
    Create a new SubsidyAttachment.
    """
    permission_required = 'scipost.can_manage_subsidies'
    model = SubsidyAttachment
    form_class = SubsidyAttachmentForm
    template_name = 'finances/subsidyattachment_form.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['countrycodes'] = [code['country'] for code in list(
            Organization.objects.all().distinct('country').values('country'))]
        return context

    def get_initial(self):
        subsidy = get_object_or_404(Subsidy, pk=self.kwargs.get('subsidy_id'))
        return {'subsidy': subsidy}

    def get_success_url(self):
        return reverse_lazy('finances:subsidy_details', kwargs={'pk': self.object.subsidy.id})


class SubsidyAttachmentUpdateView(PermissionsMixin, UpdateView):
    """
    Update a SubsidyAttachment.
    """
    permission_required = 'scipost.can_manage_subsidies'
    model = SubsidyAttachment
    form_class = SubsidyAttachmentForm
    template_name = 'finances/subsidyattachment_form.html'
    success_url = reverse_lazy('finances:subsidies')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['countrycodes'] = [code['country'] for code in list(
            Organization.objects.all().distinct('country').values('country'))]
        return context

    def get_success_url(self):
        return reverse_lazy('finances:subsidy_details', kwargs={'pk': self.object.subsidy.id})


class SubsidyAttachmentDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a SubsidyAttachment.
    """
    permission_required = 'scipost.can_manage_subsidies'
    model = SubsidyAttachment

    def get_success_url(self):
        return reverse_lazy('finances:subsidy_details', kwargs={'pk': self.object.subsidy.id})


def subsidy_attachment_toggle_public_visibility(request, attachment_id):
    """
    Method to toggle the public visibility of an attachment to a Subsidy.
    Callable by Admin and Contacts for the relevant Organization.
    """
    attachment = get_object_or_404(SubsidyAttachment, pk=attachment_id)
    if not (request.user.has_perm('scipost.can_manage_subsidies') or
            request.user.has_perm('can_view_org_contacts', attachment.subsidy.organization)):
        raise PermissionDenied
    attachment.publicly_visible = not attachment.publicly_visible
    attachment.save()
    messages.success(request, 'Attachment visibility set to %s' % attachment.publicly_visible)
    return redirect(attachment.subsidy.get_absolute_url())


def subsidy_attachment(request, subsidy_id, attachment_id):
    attachment = get_object_or_404(SubsidyAttachment.objects,
                                   subsidy__id=subsidy_id, id=attachment_id)
    if not attachment.visible_to_user(request.user):
        raise PermissionDenied
    content_type, encoding = mimetypes.guess_type(attachment.attachment.path)
    content_type = content_type or 'application/octet-stream'
    response = HttpResponse(attachment.attachment.read(), content_type=content_type)
    response["Content-Encoding"] = encoding
    response['Content-Disposition'] = ('filename=%s' % attachment.name)
    return response



############################
# Timesheets and Work Logs #
############################

@permission_required('scipost.can_view_timesheets', raise_exception=True)
def timesheets(request):
    """
    Overview of all timesheets including comments and related objects.
    """
    form = LogsFilter(request.GET or None)
    context = {'form': form}
    return render(request, 'finances/timesheets.html', context)


@permission_required('scipost.can_view_timesheets', raise_exception=True)
def timesheets_detailed(request):
    """Overview of all timesheets. """
    form = LogsFilter(request.GET or None)
    context = {'form': form}
    return render(request, 'finances/timesheets_detailed.html', context)


class LogDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkLog

    def get_object(self):
        try:
            return WorkLog.objects.get(user=self.request.user, id=slug_to_id(self.kwargs['slug']))
        except WorkLog.DoesNotExist:
            raise Http404

    def get_success_url(self):
        messages.success(self.request, 'Log deleted.')
        return self.object.content.get_absolute_url()
