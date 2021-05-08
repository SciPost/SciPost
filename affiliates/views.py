__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from guardian.decorators import permission_required_or_403
from guardian.shortcuts import assign_perm, remove_perm, get_users_with_perms

from .models import AffiliateJournal, AffiliatePublication
from .forms import AffiliateJournalAddManagerForm, AffiliateJournalAddPublicationForm


class AffiliateJournalListView(ListView):
    model = AffiliateJournal


class AffiliateJournalDetailView(DetailView):
    model = AffiliateJournal

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['journal_managers'] = get_users_with_perms(
            self.object,
            with_superusers=False
        )
        context['add_manager_form'] = AffiliateJournalAddManagerForm()
        context['add_publication_form'] = AffiliateJournalAddPublicationForm(
            initial={'journal': self.object})
        return context


@permission_required_or_403('affiliates.change_affiliatejournal',
                            (AffiliateJournal, 'slug', 'slug'))
def affiliatejournal_add_manager(request, slug):
    journal = get_object_or_404(AffiliateJournal, slug=slug)
    form = AddAffiliateJournalManagerForm(request.POST or None)
    if form.is_valid():
        assign_perm('manage_journal_content',
                    form.cleaned_data['user'], journal)
    return redirect(reverse('affiliates:journal_detail',
                            kwargs={'slug': slug}))

@permission_required_or_403('affiliates.change_affiliatejournal',
                            (AffiliateJournal, 'slug', 'slug'))
def affiliatejournal_remove_manager(request, slug, user_id):
    journal = get_object_or_404(AffiliateJournal, slug=slug)
    user = get_object_or_404(User, pk=user_id)
    remove_perm('manage_journal_content', user, journal)
    return redirect(reverse('affiliates:journal_detail',
                            kwargs={'slug': slug}))


@permission_required_or_403('affiliates.manage_journal_content',
                            (AffiliateJournal, 'slug', 'slug'))
def affiliatejournal_add_publication(request, slug):
    form = AffiliateJournalAddPublicationForm(request.POST or None)
    if form.is_valid():
        form.save()
    return redirect(reverse('affiliates:journal_detail',
                            kwargs={'slug': slug}))


class AffiliatePublicationDetailView(DetailView):
    model = AffiliatePublication
    slug_field = 'doi'
    slug_url_kwarg = 'doi'
