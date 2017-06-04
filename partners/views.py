from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, render, reverse, redirect
from django.utils import timezone

from guardian.decorators import permission_required

from .models import Partner, ProspectivePartner, ProspectiveContact, \
    ProspectivePartnerEvent, MembershipAgreement
from .forms import ProspectivePartnerForm, ProspectiveContactForm, \
    ProspectivePartnerEventForm, MembershipQueryForm


def supporting_partners(request):
    prospective_agreements = MembershipAgreement.objects.filter(
        status='Submitted').order_by('date_requested')
    context = {'prospective_partners': prospective_agreements, }
    return render(request, 'partners/supporting_partners.html', context)


@transaction.atomic
def membership_request(request):
    query_form = MembershipQueryForm(request.POST or None)
    if query_form.is_valid():
        prospartner = ProspectivePartner(
            kind=query_form.cleaned_data['partner_kind'],
            institution_name=query_form.cleaned_data['institution_name'],
            country=query_form.cleaned_data['country'],
            date_received=timezone.now(),
            status = 'requested',
        )
        prospartner.save()
        contact = ProspectiveContact(
            prospartner=prospartner,
            title=query_form.cleaned_data['title'],
            first_name=query_form.cleaned_data['first_name'],
            last_name=query_form.cleaned_data['last_name'],
            email=query_form.cleaned_data['email'],
        )
        contact.save()
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
    partners = Partner.objects.all()
    prospective_partners = ProspectivePartner.objects.all(
    ).order_by('country', 'institution_name')
    ppevent_form = ProspectivePartnerEventForm()
    agreements = MembershipAgreement.objects.all().order_by('date_requested')
    context = {'partners': partners,
               'prospective_partners': prospective_partners,
               'ppevent_form': ppevent_form,
               'agreements': agreements, }
    return render(request, 'partners/manage_partners.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
@transaction.atomic
def add_prospective_partner(request):
    form = ProspectivePartnerForm(request.POST or None,
                                  initial={'status': 'added',
                                           'kind': 'Univ. Library'})
    if form.is_valid():
        pp = form.save()
        messages.success(request, 'Prospective Partner successfully added')
#        return redirect(reverse('partners:manage'))
        return redirect(reverse('partners:add_prospartner_contact',
                                kwargs={'prospartner_id': pp.id}))
    context = {'form': form}
    return render(request, 'partners/add_prospective_partner.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
@transaction.atomic
def add_prospartner_contact(request, prospartner_id):
    prospartner = get_object_or_404(ProspectivePartner, pk=prospartner_id)
    form = ProspectiveContactForm(
        request.POST or None, initial={'prospartner': prospartner })
    if form.is_valid():
        form.save()
        messages.success(request, 'Contact successfully added to Prospective Partner')
        return redirect(reverse('partners:manage'))
    context = {'form': form,
               'prospartner': prospartner }
    return render(request, 'partners/add_prospartner_contact.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
@transaction.atomic
def add_prospartner_event(request, prospartner_id):
    prospartner = get_object_or_404(ProspectivePartner, pk=prospartner_id)
    if request.method == 'POST':
        ppevent_form = ProspectivePartnerEventForm(request.POST)
        if ppevent_form.is_valid():
            ppevent = ProspectivePartnerEvent(
                prospartner=prospartner,
                event=ppevent_form.cleaned_data['event'],
                comments=ppevent_form.cleaned_data['comments'],
                noted_on=timezone.now(),
                noted_by=request.user.contributor,)
            ppevent.save()
            return redirect(reverse('partners:manage'))
        else:
            errormessage = 'The form was invalidly filled.'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})
    else:
        errormessage = 'This view can only be posted to.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})
