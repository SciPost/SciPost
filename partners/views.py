from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, render, reverse, redirect
from django.utils import timezone

from guardian.decorators import permission_required

from .constants import PROSPECTIVE_PARTNER_REQUESTED,\
    PROSPECTIVE_PARTNER_APPROACHED, PROSPECTIVE_PARTNER_ADDED,\
    PROSPECTIVE_PARTNER_EVENT_REQUESTED, PROSPECTIVE_PARTNER_EVENT_EMAIL_SENT
from .models import Partner, ProspectivePartner, ProspectiveContact,\
                    ProspectivePartnerEvent, MembershipAgreement, Contact, Institution
from .forms import ProspectivePartnerForm, ProspectiveContactForm,\
                   EmailProspectivePartnerContactForm, PromoteToPartnerForm,\
                   ProspectivePartnerEventForm, MembershipQueryForm, PromoteToContactForm,\
                   PromoteToContactFormset, PartnerForm, ContactForm, ContactFormset,\
                   NewContactForm, InstitutionForm, ActivationForm, PartnerEventForm

from .utils import PartnerUtils


def supporting_partners(request):
    context = {}
    if request.user.groups.filter(name='Editorial Administrators').exists():
        # Show Agreements to Administrators only!
        prospective_agreements = MembershipAgreement.objects.submitted().order_by('date_requested')
        context['prospective_partners'] = prospective_agreements
    return render(request, 'partners/supporting_partners.html', context)


@login_required
@permission_required('scipost.can_read_personal_page', return_403=True)
def dashboard(request):
    '''
    This page is meant as a personal page for Partners, where they will for example be able
    to read their personal data and agreements.
    '''
    context = {}
    if request.user.has_perm('scipost.can_manage_SPB'):
        context['partners'] = Partner.objects.all()
        context['prospective_partners'] = (ProspectivePartner.objects.not_yet_partner()
                                           .order_by('country', 'institution_name'))
        context['ppevent_form'] = ProspectivePartnerEventForm()
        context['agreements'] = MembershipAgreement.objects.order_by('date_requested')
    return render(request, 'partners/dashboard.html', context)


@transaction.atomic
def membership_request(request):
    query_form = MembershipQueryForm(request.POST or None)
    if query_form.is_valid():
        prospartner = ProspectivePartner(
            kind=query_form.cleaned_data['partner_kind'],
            institution_name=query_form.cleaned_data['institution_name'],
            country=query_form.cleaned_data['country'],
            date_received=timezone.now(),
            status=PROSPECTIVE_PARTNER_REQUESTED,
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
        prospartnerevent = ProspectivePartnerEvent(
            prospartner=prospartner,
            event=PROSPECTIVE_PARTNER_EVENT_REQUESTED)
        prospartnerevent.save()
        ack_message = ('Thank you for your SPB Membership query. '
                       'We will get back to you in the very near future '
                       'with further details.')
        context = {'ack_message': ack_message}
        return render(request, 'scipost/acknowledgement.html', context)
    context = {'query_form': query_form}
    return render(request, 'partners/membership_request.html', context)


@permission_required('scipost.can_promote_prospect_to_partner', return_403=True)
@transaction.atomic
def promote_prospartner(request, prospartner_id):
    prospartner = get_object_or_404(ProspectivePartner.objects.not_yet_partner(),
                                    pk=prospartner_id)
    form = PromoteToPartnerForm(request.POST or None, instance=prospartner)
    ContactModelFormset = modelformset_factory(ProspectiveContact, PromoteToContactForm,
                                               formset=PromoteToContactFormset, extra=0)
    contact_formset = ContactModelFormset(request.POST or None,
                                          queryset=prospartner.prospective_contacts.all())
    if form.is_valid() and contact_formset.is_valid():
        partner, institution = form.promote_to_partner(request.user)
        contacts = contact_formset.promote_contacts(partner)

        # partner.send_mail()
        # contacts.send_mail()
        messages.success(request, ('<h3>Upgraded Partner %s</h3>'
                                   '%i contacts have received a validation mail.') %
                                  (str(partner), len(contacts)))
        return redirect(reverse('partners:dashboard'))
    context = {'form': form, 'contact_formset': contact_formset}
    return render(request, 'partners/promote_prospartner.html', context)


###############
# Partner views
###############
@permission_required('scipost.can_view_partners', return_403=True)
def partner_view(request, partner_id):
    partner = get_object_or_404(Partner, id=partner_id)
    form = PartnerEventForm(request.POST or None)
    if form.is_valid():
        event = form.save(commit=False)
        event.partner = partner
        event.noted_by = request.user
        event.save()
        messages.success(request, 'Added a new event to Partner.')
        return redirect(partner.get_absolute_url())
    context = {
        'partner': partner,
        'form': form
    }
    return render(request, 'partners/partners_detail.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
@transaction.atomic
def partner_edit(request, partner_id):
    partner = get_object_or_404(Partner, id=partner_id)

    # Start/fill forms
    form = PartnerForm(request.POST or None, instance=partner)
    ContactModelFormset = modelformset_factory(Contact, ContactForm, can_delete=True, extra=0,
                                               formset=ContactFormset)
    contact_formset = ContactModelFormset(request.POST or None, partner=partner,
                                          queryset=partner.contact_set.all())

    # Validate forms for POST request
    if form.is_valid() and contact_formset.is_valid():
        form.save()
        contact_formset.save()
        messages.success(request, 'Partner saved')
        return redirect(reverse('partners:partner_edit', args=(partner.id,)))
    context = {
        'form': form,
        'contact_formset': contact_formset
    }
    return render(request, 'partners/partner_edit.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
def partner_add_contact(request, partner_id):
    partner = get_object_or_404(Partner, id=partner_id)
    form = NewContactForm(request.POST or None, partner=partner)
    if form.is_valid():
        contact = form.save()
        messages.success(request, '<h3>Created contact: %s</h3>Email has been sent.'
                                  % str(contact))
        return redirect(reverse('partners:dashboard'))
    context = {
        'partner': partner,
        'form': form
    }
    return render(request, 'partners/partner_add_contact.html', context)


###################
# Institution Views
###################
@permission_required('scipost.can_manage_SPB', return_403=True)
def institution_edit(request, institution_id):
    institution = get_object_or_404(Institution, id=institution_id)
    form = InstitutionForm(request.POST or None, instance=institution)
    if form.is_valid():
        form.save()
        return redirect(reverse('partners:dashboard'))
    context = {
        'form': form
    }
    return render(request, 'partners/institution_edit.html', context)


###########################
# Prospective Partner Views
###########################
@permission_required('scipost.can_manage_SPB', return_403=True)
def add_prospective_partner(request):
    form = ProspectivePartnerForm(request.POST or None)
    if form.is_valid():
        pp = form.save()
        messages.success(request, 'Prospective Partner successfully added')
        return redirect(reverse('partners:add_prospartner_contact',
                                kwargs={'prospartner_id': pp.id}))
    context = {'form': form}
    return render(request, 'partners/add_prospective_partner.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
def add_prospartner_contact(request, prospartner_id):
    prospartner = get_object_or_404(ProspectivePartner, pk=prospartner_id)
    form = ProspectiveContactForm(request.POST or None, initial={'prospartner': prospartner})
    if form.is_valid():
        form.save()
        messages.success(request, 'Contact successfully added to Prospective Partner')
        return redirect(reverse('partners:dashboard'))
    context = {'form': form, 'prospartner': prospartner}
    return render(request, 'partners/add_prospartner_contact.html', context)


@permission_required('scipost.can_email_prospartner_contact', return_403=True)
@transaction.atomic
def email_prospartner_contact(request, contact_id):
    contact = get_object_or_404(ProspectiveContact, pk=contact_id)
    form = EmailProspectivePartnerContactForm(request.POST or None)
    if form.is_valid():
        comments = 'Email sent to %s.' % str(contact)
        prospartnerevent = ProspectivePartnerEvent(
            prospartner=contact.prospartner,
            event=PROSPECTIVE_PARTNER_EVENT_EMAIL_SENT,
            comments=comments,
            noted_on=timezone.now(),
            noted_by=request.user.contributor)
        prospartnerevent.save()
        if contact.prospartner.status in [PROSPECTIVE_PARTNER_REQUESTED,
                                          PROSPECTIVE_PARTNER_ADDED]:
            contact.prospartner.status = PROSPECTIVE_PARTNER_APPROACHED
            contact.prospartner.save()
        PartnerUtils.load({'contact': contact,
                           'email_subject': form.cleaned_data['email_subject'],
                           'message': form.cleaned_data['message'],
                           'include_SPB_summary': form.cleaned_data['include_SPB_summary']})

        PartnerUtils.email_prospartner_contact()
        messages.success(request, 'Email successfully sent')
        return redirect(reverse('partners:dashboard'))
    context = {'contact': contact, 'form': form}
    return render(request, 'partners/email_prospartner_contact.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
@transaction.atomic
def add_prospartner_event(request, prospartner_id):
    prospartner = get_object_or_404(ProspectivePartner, pk=prospartner_id)
    if request.method == 'POST':
        ppevent_form = ProspectivePartnerEventForm(request.POST)
        if ppevent_form.is_valid():
            ppevent = ppevent_form.save(commit=False)
            ppevent.prospartner = prospartner
            ppevent.noted_by = request.user.contributor
            ppevent.save()
            prospartner.update_status_from_event(ppevent.event)
            prospartner.save()
            return redirect(reverse('partners:dashboard'))
        else:
            errormessage = 'The form was invalidly filled.'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})
    errormessage = 'This view can only be posted to.'
    return render(request, 'scipost/error.html', {'errormessage': errormessage})


#########
# Account
#########
def activate_account(request, activation_key):
    contact = get_object_or_404(Contact, user__is_active=False,
                                activation_key=activation_key,
                                user__email__icontains=request.GET.get('email', None))

    # TODO: Key Expires fallback
    form = ActivationForm(request.POST or None, instance=contact.user)
    if form.is_valid():
        form.activate_user()
        messages.success(request, '<h3>Thank you for registration</h3>.')
        return redirect(reverse('partners:dashboard'))
    context = {
        'contact': contact,
        'form': form
    }
    return render(request, 'partners/activate_account.html', context)
