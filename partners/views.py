from django.contrib import messages
from django.shortcuts import render, reverse, redirect
from django.utils import timezone

from guardian.decorators import permission_required

from .models import Partner, ProspectivePartner, MembershipAgreement
from .forms import ProspectivePartnerForm, MembershipQueryForm


def supporting_partners(request):
    prospective_agreements = MembershipAgreement.objects.filter(
        status='Submitted').order_by('date_requested')
    context = {'prospective_partners': prospective_agreements, }
    return render(request, 'partners/supporting_partners.html', context)


def membership_request(request):
    query_form = MembershipQueryForm(request.POST or None)
    if query_form.is_valid():
        query = ProspectivePartner(
            title=query_form.cleaned_data['title'],
            first_name=query_form.cleaned_data['first_name'],
            last_name=query_form.cleaned_data['last_name'],
            email=query_form.cleaned_data['email'],
            partner_type=query_form.cleaned_data['partner_type'],
            institution_name=query_form.cleaned_data['institution_hame'],
            country=query_form.cleaned_data['country'],
            date_received=timezone.now(),
        )
        query.save()
        ack_message = ('Thank you for your SPB Membership query. '
                       'We will get back to you in the very near future '
                       'with further details.')
        context = {'ack_message': ack_message, }
        return render(request, 'scipost/acknowledgement.html', context)
    context = {'query_form': query_form}
    return render(request, 'partners/membership_request.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
def manage(request):
    """
    Lists relevant info regarding management of Supporting Partners Board.
    """
    partners = Partner.objects.all().order_by('country', 'institution_name')
    prospective_partners = ProspectivePartner.objects.filter(
        processed=False).order_by('date_received')
    agreements = MembershipAgreement.objects.all().order_by('date_requested')
    context = {'partners': partners,
               'prospective_partners': prospective_partners,
               'agreements': agreements, }
    return render(request, 'partners/manage_partners.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
def add_prospective_partner(request):
    form = ProspectivePartnerForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Prospective Partners successfully added')
        return redirect(reverse('partners:manage'))
    context = {'form': form}
    return render(request, 'partners/add_prospective_partner.html', context)
