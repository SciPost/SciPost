import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from .models import *
from .forms import *


###########
# Reports
###########


def submit_report(request, submission_id):
    submission = get_object_or_404 (Submission, pk=submission_id)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            author = Contributor.objects.get(user=request.user)
            newreport = Report (
                submission = submission,
                author = author,
                qualification = form.cleaned_data['qualification'],
                strengths = form.cleaned_data['strengths'],
                weaknesses = form.cleaned_data['weaknesses'],
                report = form.cleaned_data['report'],
                requested_changes = form.cleaned_data['requested_changes'],
                recommendation = form.cleaned_data['recommendation'],
                date_submitted = timezone.now(),
                )
            newreport.save()
            author.nr_reports = Report.objects.filter(author=author).count()
            author.save()
            request.session['submission_id'] = submission_id
            return HttpResponseRedirect(reverse('reports:submit_report_ack'))

    else:
        form = ReportForm()
    context = {'submission': submission, 'form': form }
    return render(request, 'reports/submit_report.html', context)


def submit_report_ack(request):
#    submission_id = request.session['submission_id']
#    context = {'submission': Submission.objects.get(pk=submission_id) }
    context = {}
    return render(request, 'reports/submit_report_ack.html', context)


def vet_submitted_reports(request):
    contributor = Contributor.objects.get(user=request.user)
    submitted_reports_to_vet = Report.objects.filter(status=0)
    form = VetReportForm()
    context = {'contributor': contributor, 'submitted_reports_to_vet': submitted_reports_to_vet, 'form': form }
    return(render(request, 'reports/vet_submitted_reports.html', context))


def vet_submitted_report_ack(request, report_id):
    if request.method == 'POST':
        form = VetReportForm(request.POST)
        report = Report.objects.get(pk=report_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the report as is
                report.status = 1
                report.save()
            elif form.cleaned_data['action_option'] == '2':
                # the report is simply rejected
                report.status = form.cleaned_data['refusal_reason']
                report.save()
                # email report author

    context = {}
    return render(request, 'reports/vet_submitted_report_ack.html', context)


