__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, DeleteView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404

from scipost.mixins import PermissionsMixin

from .forms import InstitutionMergeForm, InstitutionOrganizationSelectForm
from .models import Institution


class InstitutionListView(ListView):
    queryset = Institution.objects.has_publications()
    paginate_by = 20


class InstitutionDetailView(DetailView):
    model = Institution
    pk_url_kwarg = 'institution_id'


class InstitutionDeleteView(PermissionsMixin, DeleteView):
    model = Institution
    permission_required = 'scipost.can_manage_affiliations'
    pk_url_kwarg = 'institution_id'
    success_url = reverse_lazy('affiliations:institutions_without_organization')


@method_decorator(permission_required('scipost.can_manage_affiliations'), name='dispatch')
class InstitutionUpdateView(UpdateView):
    model = Institution
    pk_url_kwarg = 'institution_id'
    fields = [
        'name',
        'acronym',
        'country',
    ]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['merge_form'] = InstitutionMergeForm()
        return context

    def form_valid(self, *args, **kwargs):
        messages.success(self.request, 'Institution saved')
        return super().form_valid(*args, **kwargs)


@permission_required('scipost.can_manage_affiliations')
def merge_institutions(request, institution_id):
    """
    Merge Affiliation (affiliation_id) into the Affliation chosen in the form.
    """
    institution = get_object_or_404(Institution, id=institution_id)
    form = InstitutionMergeForm(request.POST or None, instance=institution)
    if form.is_valid():
        form.save()
        messages.success(request, 'Institution {a} merged into {b}'.format(
            a=form.cleaned_data.get('institution', '?'), b=institution))

    return redirect(reverse('affiliations:institution_edit', args=(institution.id,)))


class InstitutionWithoutOrganizationListView(ListView):
    queryset = Institution.objects.filter(organization=None)
    paginate_by = 20
    template_name = 'affiliations/institutions_without_organization_list.html'


class LinkInstitutionToOrganizationView(PermissionsMixin, UpdateView):
    """
    For an existing Institution instance, specify the link to an Organization.
    """
    permission_required = 'scipost.can_manage_affiliations'
    model = Institution
    form_class = InstitutionOrganizationSelectForm
    template_name = 'affiliations/institution_link_organization.html'
    success_url = reverse_lazy('affiliations:institutions_without_organization')

    def form_valid(self, form):
        form.instance.organization = form.cleaned_data['organization']
        return super().form_valid(form)
