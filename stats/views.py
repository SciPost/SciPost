import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render

from journals.constants import SCIPOST_JOURNALS_SUBMIT
from journals.models import Journal, Volume, Issue, Publication
from submissions.models import Submission


@permission_required('scipost.can_view_statistics', raise_exception=True)
def statistics(request, journal_doi_label=None, volume_nr=None, issue_nr=None, year=None):
    journals = Journal.objects.all()
    context = {
        'journals': journals,
    }
    if journal_doi_label:
        journal = get_object_or_404(Journal, doi_label=journal_doi_label)
        context['journal'] = journal
        if year:
            context['year'] = year
            submissions = Submission.objects.filter(submitted_to_journal=journal_doi_label
            ).originally_submitted(datetime.date(int(year), 1, 1), datetime.date(int(year), 12, 31))
            context['submissions'] = submissions
            nr_ref_inv = 0
            nr_acc = 0
            nr_dec = 0
            nr_pen = 0
            nr_rep_obt = 0
            nr_rep_obt_inv = 0
            nr_rep_obt_con = 0
            nr_rep_ref = 0
            nr_aw_vet = 0
            for submission in submissions:
                nr_ref_inv += submission.referee_invitations.count()
                nr_acc += submission.count_accepted_invitations()
                nr_dec += submission.count_declined_invitations()
                nr_pen += submission.count_pending_invitations()
                nr_rep_obt += submission.count_obtained_reports()
                nr_rep_obt_inv += submission.count_invited_reports()
                nr_rep_obt_con += submission.count_contrib_reports()
            context['nr_ref_inv'] = nr_ref_inv
            context['nr_acc'] = nr_acc
            context['nr_dec'] = nr_dec
            context['nr_pen'] = nr_pen
            context['nr_rep_obt'] = nr_rep_obt
            context['nr_rep_obt_inv'] = nr_rep_obt_inv
            context['nr_rep_obt_con'] = nr_rep_obt_con
        if volume_nr:
            volume = get_object_or_404(Volume, in_journal=journal,
                                       number=volume_nr)
            context['volume'] = volume
            if issue_nr:
                issue = get_object_or_404(Issue, in_volume=volume,
                                          number=issue_nr)
                context['issue'] = issue
    return render(request, 'stats/statistics.html', context)
