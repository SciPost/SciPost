from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render

from journals.models import Journal, Volume, Issue, Publication
from submissions.models import Submission


@permission_required('scipost.can_oversee_refereeing', raise_exception=True)
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
            submissions = Submission.objects.filter(
                submitted_to_journal=journal,
                submission_date__year=year,
            )
            context['submissions'] = submissions
        if volume_nr:
            volume = get_object_or_404(Volume, in_journal=journal,
                                       number=volume_nr)
            context['volume'] = volume
            if issue_nr:
                issue = get_object_or_404(Issue, in_volume=volume,
                                          number=issue_nr)
                context['issue'] = issue
    return render(request, 'stats/statistics.html', context)
